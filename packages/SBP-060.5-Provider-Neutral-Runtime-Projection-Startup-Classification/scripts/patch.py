#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
web = root / 'seymour-blockchain-manager' / 'data' / 'web'

# 1) Provider-neutral runtime registry. BTC is probed through Docker socket;
# BCH keeps its mature probe and is projected through the same registry.
(web / 'runtime_registry.py').write_text(r'''from __future__ import annotations
import json
import os
import socket
from pathlib import Path
from typing import Any
from urllib.parse import quote

DOCKER_SOCKET = Path(os.environ.get("DOCKER_SOCKET", "/var/run/docker.sock"))

RUNTIMES = {
    "bitcoin-mainnet": {
        "appId": os.environ.get("BTC_APP_ID", "seymour-bitcoin-node"),
        "container": os.environ.get("BTC_NODE_CONTAINER", "seymour-bitcoin-node_node_1"),
        "dataPath": Path(os.environ.get("BTC_DATA_PATH", "/bitcoin-data")),
    },
}

def _decode_chunked(body: bytes) -> bytes:
    out = bytearray()
    pos = 0
    while pos < len(body):
        end = body.find(b"\r\n", pos)
        if end < 0:
            break
        try:
            size = int(body[pos:end].split(b";", 1)[0], 16)
        except Exception:
            break
        pos = end + 2
        if size == 0:
            break
        out.extend(body[pos:pos + size])
        pos += size + 2
    return bytes(out)

def docker_container(name: str) -> dict[str, Any]:
    out = {
        "available": DOCKER_SOCKET.exists(),
        "found": False,
        "name": name,
        "status": "not-found",
        "running": False,
        "health": "unknown",
    }
    if not DOCKER_SOCKET.exists():
        return out
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect(str(DOCKER_SOCKET))
        path = f"/containers/{quote(name, safe='')}/json"
        sock.sendall(
            f"GET {path} HTTP/1.1\r\nHost: docker\r\nConnection: close\r\n\r\n".encode()
        )
        chunks = []
        while True:
            chunk = sock.recv(65536)
            if not chunk:
                break
            chunks.append(chunk)
        sock.close()
        raw = b"".join(chunks)
        head, _, body = raw.partition(b"\r\n\r\n")
        try:
            code = int(head.splitlines()[0].split()[1])
        except Exception:
            code = 0
        if code != 200:
            return out
        headers = {}
        for line in head.splitlines()[1:]:
            if b":" not in line:
                continue
            key, value = line.split(b":", 1)
            headers[key.decode().strip().lower()] = value.decode().strip().lower()
        if headers.get("transfer-encoding") == "chunked":
            body = _decode_chunked(body)
        payload = json.loads(body.decode())
        state = payload.get("State") if isinstance(payload.get("State"), dict) else {}
        health = state.get("Health") if isinstance(state.get("Health"), dict) else {}
        out.update({
            "found": True,
            "status": str(state.get("Status") or "unknown"),
            "running": bool(state.get("Running")),
            "health": str(health.get("Status") or "none"),
            "containerId": str(payload.get("Id") or "")[:12] or None,
        })
        return out
    except Exception as exc:
        out["status"] = "docker-error"
        out["error"] = str(exc)
        return out

def btc_telemetry() -> dict[str, Any]:
    runtime = RUNTIMES["bitcoin-mainnet"]
    container = docker_container(runtime["container"])
    installed = bool(container.get("found"))
    running = bool(container.get("running"))
    if not installed:
        state = "not-installed"
        reason = "Runtime is not installed."
    elif not running:
        state = "stopped"
        reason = "Runtime is installed but stopped."
    elif container.get("health") in {"starting", "unknown"}:
        state = "starting"
        reason = "Runtime container is starting."
    else:
        # RPC telemetry will be layered onto this provider-neutral registry when
        # BTC is installed and its credentials/runtime binding are available.
        state = "running"
        reason = "Runtime container is running; RPC telemetry is not configured yet."
    return {
        "providerId": "bitcoin-mainnet",
        "appId": runtime["appId"],
        "installed": installed,
        "running": running,
        "lifecycleStatus": state,
        "runtimeState": state,
        "runtimeStateReason": reason,
        "runtimeRpcReachable": False,
        "runtimeRpcHealthy": False,
        "operationalState": {
            "state": state,
            "reason": reason,
            "installed": installed,
            "running": running,
            "containerHealth": container.get("health"),
        },
        "container": container,
        "rpc": {"reachable": False, "healthy": False, "status": "not-configured"},
        "sync": {"height": None, "headers": None, "progressPercent": None, "initialBlockDownload": None},
        "peers": None,
        "mempool": None,
        "data": {"path": str(runtime["dataPath"]), "usedBytes": 0},
    }

def dashboard_runtimes(*, bch_telemetry) -> dict[str, Any]:
    return {
        "bitcoin-mainnet": btc_telemetry(),
        "bitcoin-cash-mainnet": bch_telemetry(),
    }
''')

# 2) Telemetry: socket-native Docker check and registry projection.
p = web / 'telemetry.py'
t = p.read_text()
if 'from runtime_registry import dashboard_runtimes' not in t:
    anchor = 'from bch_runtime_probe import probe as probe_bch_runtime\n'
    if anchor not in t:
        raise SystemExit('telemetry import anchor not found')
    t = t.replace(anchor, anchor + 'from runtime_registry import dashboard_runtimes\n', 1)
old = '''def docker_available() -> bool:\n    if not DOCKER_SOCKET.exists():\n        return False\n\n    try:\n        result = subprocess.run(\n            [\n                "docker",\n                "version",\n                "--format",\n                "{{.Server.Version}}",\n            ],\n            capture_output=True,\n            text=True,\n            timeout=3,\n            check=False,\n        )\n        return result.returncode == 0\n    except Exception:\n        return False\n'''
new = '''def docker_available() -> bool:\n    if not DOCKER_SOCKET.exists():\n        return False\n\n    try:\n        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)\n        sock.settimeout(2)\n        sock.connect(str(DOCKER_SOCKET))\n        sock.close()\n        return True\n    except Exception:\n        return False\n'''
if old in t:
    t = t.replace(old, new, 1)
old = '''def dashboard_payload() -> dict[str, Any]:\n    return {\n        "generatedAt": time.time(),\n        "host": host_telemetry(),\n        "providers": {\n            "bitcoin-cash-mainnet": bch_telemetry(),\n        },\n    }\n'''
new = '''def dashboard_payload() -> dict[str, Any]:\n    return {\n        "generatedAt": time.time(),\n        "host": host_telemetry(),\n        "providers": dashboard_runtimes(\n            bch_telemetry=bch_telemetry,\n        ),\n    }\n'''
if old not in t:
    raise SystemExit('dashboard payload anchor not found')
t = t.replace(old, new, 1)
p.write_text(t)

# 3) BCH: status service already knows "starting" while RPC verifies blocks.
p = web / 'bch_runtime_probe.py'
t = p.read_text()
old = ''' result = {"providerId":"bitcoin-cash-mainnet","appId":"seymour-bch-node","installed":installed,"running":running,"lifecycleStatus":lifecycle,"container":container,"rpc":{"reachable":rpc,"probe":rpc_probe,"health":legacy_health,"status":legacy_status}}\n result["operationalState"] = normalize_runtime_state(result)\n result["lifecycleStatus"] = result["operationalState"]["state"]\n return result\n'''
new = ''' result = {"providerId":"bitcoin-cash-mainnet","appId":"seymour-bch-node","installed":installed,"running":running,"lifecycleStatus":lifecycle,"container":container,"rpc":{"reachable":rpc,"probe":rpc_probe,"health":legacy_health,"status":legacy_status}}\n result["operationalState"] = normalize_runtime_state(result)\n status_payload = legacy_status.get("payload") if isinstance(legacy_status.get("payload"),dict) else {}\n status_state = str(status_payload.get("status") or "").strip().lower()\n if running and not rpc and status_state in {"starting","verifying","warming-up","recovering"}:\n  result["operationalState"] = {**result["operationalState"],"state":"starting","reason":"Runtime is verifying or warming existing blockchain data."}\n result["lifecycleStatus"] = result["operationalState"]["state"]\n return result\n'''
if old not in t:
    raise SystemExit('BCH startup classification anchor not found')
p.write_text(t.replace(old, new, 1))

# 4) Frontend: installed means telemetry says installed; render all cards.
p = web / 'app.js'
t = p.read_text()
old = '''function installedProviders() {\n  return state.providers.filter(\n    (provider) => provider.availability === "live"\n  );\n}\n'''
new = '''function installedProviders() {\n  return state.providers.filter((provider) => {\n    if (provider.availability !== "live") return false;\n    const telemetry = providerTelemetry(provider.providerId);\n    return telemetry?.installed === true;\n  });\n}\n'''
if old not in t:
    raise SystemExit('installedProviders anchor not found')
t = t.replace(old, new, 1)
start = t.find('function renderRuntimeFocus() {')
end = t.find('\nfunction ', start + 1)
if start < 0 or end < 0:
    raise SystemExit('renderRuntimeFocus boundary not found')
body = r'''function renderRuntimeFocus() {
  const target = document.getElementById("runtimeFocus");
  if (!target) return;

  const live = installedProviders();
  if (!live.length) {
    target.innerHTML = `
      <div class="empty-runtime-focus">
        No managed blockchain runtime is currently installed.
      </div>
    `;
    return;
  }

  const renderCard = (provider) => {
    const presentation = presentedRuntime(provider);
    const telemetry = presentation.telemetry || {};
    const sync = telemetry.sync || {};
    const stateLabel = lifecycleLabel(presentation.state);
    const rawProgress = Number(sync.progressPercent);
    const progress = Number.isFinite(rawProgress) ? rawProgress : null;
    const rawHeight = Number(sync.height);
    const rawHeaders = Number(sync.headers);
    const height = Number.isFinite(rawHeight) ? rawHeight : null;
    const headers = Number.isFinite(rawHeaders) ? rawHeaders : null;
    const peers = telemetry.peers ?? "—";
    const rpcHealthy =
      telemetry.runtimeRpcHealthy ??
      telemetry.rpc?.healthy ??
      telemetry.rpc?.reachable ??
      false;

    return `
      <article class="runtime-focus-card ${presentation.state}">
        <div class="runtime-focus-heading">
          <div>
            <p class="provider-family">managed runtime</p>
            <h2>${provider.displayName}</h2>
            <p class="implementation">${provider.implementation} ${provider.nodeVersion}</p>
          </div>
          <span class="status-pill">${stateLabel}</span>
        </div>
        ${
          presentation.state === "syncing" && progress !== null
            ? `<div class="runtime-focus-progress">${progressBar(progress, "Blockchain sync")}<div class="runtime-focus-blocks"><span>Blocks</span><strong>${height !== null && headers !== null ? `${height.toLocaleString()} / ${headers.toLocaleString()}` : "Telemetry warming up"}</strong></div></div>`
            : ["starting", "recovering"].includes(presentation.state)
              ? `<div class="telemetry-grace-note">Runtime is verifying or warming existing blockchain data.</div>`
              : ""
        }
        <div class="runtime-focus-kpis">
          <article><span>Runtime</span><strong>${stateLabel}</strong></article>
          <article><span>RPC</span><strong class="${rpcHealthy ? "metric-good" : "metric-bad"}">${rpcHealthy ? "Healthy" : ["starting", "recovering"].includes(presentation.state) ? "Warming up" : "Unavailable"}</strong></article>
          <article><span>Peers</span><strong>${peers}</strong></article>
          <article><span>Chain data</span><strong>${formatBytes(telemetry.data?.usedBytes)}</strong></article>
        </div>
        <div class="runtime-focus-actions">
          <button class="secondary" data-focus-details="${provider.providerId}">Open</button>
          <button class="secondary" data-focus-operations="${provider.providerId}">Operations</button>
          <button class="primary" data-focus-manage="${provider.providerId}">Manage</button>
        </div>
      </article>
    `;
  };

  target.innerHTML = live.map(renderCard).join("");
}
'''
p.write_text(t[:start] + body + t[end:])
print('SBP-060.5 provider-neutral runtime projection patch: PASS')
