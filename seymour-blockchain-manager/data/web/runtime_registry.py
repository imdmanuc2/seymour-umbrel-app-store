from __future__ import annotations
import json
import os
import socket
from pathlib import Path
from typing import Any
from runtime_health import runtime_health
from urllib.parse import quote
from urllib import request

DOCKER_SOCKET = Path(os.environ.get("DOCKER_SOCKET", "/var/run/docker.sock"))

BTC_STATUS_PORT=int(os.environ.get("BTC_STATUS_PORT","8080"))
BTC_STATUS_TIMEOUT_SECONDS=float(os.environ.get("BTC_STATUS_TIMEOUT_SECONDS","10"))

RUNTIMES = {
    "bitcoin-mainnet": {
        "appId": os.environ.get("BTC_APP_ID", "seymour-bitcoin-node"),
        "service": os.environ.get("BTC_NODE_SERVICE", "node"),
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

def _docker_request(path: str) -> tuple[int, Any]:
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(3)
    sock.connect(str(DOCKER_SOCKET))
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

    headers = {}
    for line in head.splitlines()[1:]:
        if b":" not in line:
            continue
        key, value = line.split(b":", 1)
        headers[key.decode().strip().lower()] = value.decode().strip().lower()

    if headers.get("transfer-encoding") == "chunked":
        body = _decode_chunked(body)

    if not body:
        return code, None

    try:
        return code, json.loads(body.decode())
    except Exception:
        return code, None


def docker_compose_container(
    app_id: str,
    service: str,
) -> dict[str, Any]:
    out = {
        "available": DOCKER_SOCKET.exists(),
        "found": False,
        "appId": app_id,
        "service": service,
        "name": None,
        "status": "not-found",
        "running": False,
        "health": "unknown",
    }

    if not DOCKER_SOCKET.exists():
        return out

    try:
        filters = json.dumps({
            "label": [
                f"com.docker.compose.project={app_id}",
                f"com.docker.compose.service={service}",
            ]
        })

        path = (
            "/containers/json?all=1&filters="
            + quote(filters, safe="")
        )

        code, payload = _docker_request(path)

        if code != 200 or not isinstance(payload, list):
            return out

        candidates = [
            item
            for item in payload
            if isinstance(item, dict)
        ]

        if not candidates:
            return out

        def rank(item: dict[str, Any]) -> tuple[int, int]:
            state = str(item.get("State") or "")
            status = str(item.get("Status") or "")
            return (
                1 if state == "running" else 0,
                1 if "healthy" in status.lower() else 0,
            )

        candidate = max(candidates, key=rank)

        container_id = str(candidate.get("Id") or "")
        if not container_id:
            return out

        code, detail = _docker_request(
            f"/containers/{quote(container_id, safe='')}/json"
        )

        if code != 200 or not isinstance(detail, dict):
            return out

        state = (
            detail.get("State")
            if isinstance(detail.get("State"), dict)
            else {}
        )
        health = (
            state.get("Health")
            if isinstance(state.get("Health"), dict)
            else {}
        )

        names = detail.get("Name")
        name = (
            str(names).lstrip("/")
            if names
            else None
        )

        out.update({
            "found": True,
            "name": name,
            "status": str(state.get("Status") or "unknown"),
            "running": bool(state.get("Running")),
            "health": str(health.get("Status") or "none"),
            "containerId": container_id[:12] or None,
            "discovery": "compose-labels",
        })

        return out

    except Exception as exc:
        out["status"] = "docker-error"
        out["error"] = str(exc)
        return out

def _btc_status_url(runtime: dict[str, Any]) -> str:
    app_id = str(runtime["appId"])
    host = os.environ.get("BTC_STATUS_HOST", f"{app_id}-status")
    return f"http://{host}:{BTC_STATUS_PORT}/api/status"


def _read_btc_status(runtime: dict[str, Any]) -> dict[str, Any]:
    url = _btc_status_url(runtime)
    try:
        with request.urlopen(url, timeout=BTC_STATUS_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode())
        return payload if isinstance(payload, dict) else {"error": "invalid-status-payload"}
    except Exception as exc:
        return {
            "error": str(exc),
            "runtimeRpcReachable": False,
            "runtimeRpcHealthy": False,
        }


def btc_telemetry() -> dict[str, Any]:
    runtime = RUNTIMES["bitcoin-mainnet"]
    container = docker_compose_container(
        str(runtime["appId"]),
        str(runtime["service"]),
    )
    installed = bool(container.get("found"))
    running = bool(container.get("running"))
    status = _read_btc_status(runtime) if installed and running else {}

    if not installed:
        state, reason = "not-installed", "Runtime is not installed."
    elif not running:
        state, reason = "stopped", "Runtime is installed but stopped."
    else:
        state = str(status.get("runtimeState") or "starting")
        reason = str(
            status.get("runtimeStateReason")
            or status.get("error")
            or "Bitcoin telemetry is initializing."
        )

    rpc_reachable = bool(status.get("runtimeRpcReachable"))
    rpc_healthy = bool(status.get("runtimeRpcHealthy"))
    verification = status.get("verificationProgress")
    progress = (
        float(verification) * 100.0
        if isinstance(verification, (int, float))
        else None
    )

    sync = {
        "height": status.get("blocks"),
        "headers": status.get("headers"),
        "progressPercent": progress,
        "initialBlockDownload": status.get("initialBlockDownload"),
    }

    storage = (
        status.get("storage")
        if isinstance(status.get("storage"), dict)
        else {}
    )

    health = runtime_health(
        runtime_state=state,
        rpc_reachable=rpc_reachable,
        rpc_healthy=rpc_healthy,
        sync=sync,
        sync_analysis={},
        storage=storage,
        telemetry_stale=bool(status.get("telemetryStale")),
        runtime_reason=reason,
    )

    chain_size = status.get("chainSizeBytes")
    if not isinstance(chain_size, (int, float)):
        chain_size = 0

    return {
        "providerId": "bitcoin-mainnet",
        "appId": runtime["appId"],
        "installed": installed,
        "running": running,
        "lifecycleStatus": state,
        "runtimeState": state,
        "runtimeStateReason": reason,
        "health": health,
        "telemetryFresh": status.get("telemetryFresh", False),
        "telemetryStale": status.get("telemetryStale", False),
        "telemetryAgeSeconds": status.get("telemetryAgeSeconds"),
        "telemetrySource": status.get("telemetrySource", "unavailable"),
        "runtimeRpcReachable": rpc_reachable,
        "runtimeRpcHealthy": rpc_healthy,
        "runtimeInitialBlockDownload": sync["initialBlockDownload"],
        "runtimeVerificationProgress": verification,
        "operationalState": {
            "state": state,
            "reason": reason,
            "installed": installed,
            "running": running,
            "containerHealth": container.get("health"),
            "rpcReachable": rpc_reachable,
            "rpcHealthy": rpc_healthy,
            "initialBlockDownload": sync["initialBlockDownload"],
            "verificationProgress": verification,
        },
        "container": container,
        "rpc": {"reachable": rpc_reachable, "healthy": rpc_healthy},
        "sync": sync,
        "peers": status.get("peers"),
        "mempool": None,
        "data": {
            "path": str(runtime["dataPath"]),
            "usedBytes": int(chain_size),
        },
        "subversion": status.get("subversion"),
    }


def dashboard_runtimes(*, bch_telemetry) -> dict[str, Any]:
    return {
        "bitcoin-mainnet": btc_telemetry(),
        "bitcoin-cash-mainnet": bch_telemetry(),
    }
