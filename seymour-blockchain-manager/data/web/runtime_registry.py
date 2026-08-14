from __future__ import annotations
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
