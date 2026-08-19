from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import time
import urllib.request
from pathlib import Path

RPC_HOST = os.environ.get("XMR_RPC_HOST", "node")
RPC_PORT = int(os.environ.get("XMR_RPC_PORT", "18081"))
DATA_PATH = Path(os.environ.get("XMR_DATA_PATH", "/node-data"))
RPC_TIMEOUT = float(os.environ.get("XMR_RPC_TIMEOUT_SECONDS", "15"))


def rpc(method: str) -> dict:
    body = json.dumps({
        "jsonrpc": "2.0",
        "id": "seymour",
        "method": method,
    }).encode()

    req = urllib.request.Request(
        f"http://{RPC_HOST}:{RPC_PORT}/json_rpc",
        data=body,
        headers={"Content-Type": "application/json"},
    )

    with urllib.request.urlopen(req, timeout=RPC_TIMEOUT) as response:
        payload = json.loads(response.read().decode())

    result = payload.get("result")
    if not isinstance(result, dict):
        raise RuntimeError("invalid-monero-rpc-payload")
    return result


def storage() -> dict:
    stat = os.statvfs(DATA_PATH)
    total = stat.f_blocks * stat.f_frsize
    free = stat.f_bavail * stat.f_frsize
    return {
        "path": str(DATA_PATH),
        "totalBytes": total,
        "filesystemUsedBytes": total - free,
        "freeBytes": free,
        "healthy": True,
    }


def status_payload() -> dict:
    try:
        info = rpc("get_info")
        height = info.get("height")
        target_height = info.get("target_height")
        synchronized = bool(info.get("synchronized"))

        runtime_state = "running" if synchronized else "syncing"
        reason = (
            "Monero daemon is synchronized."
            if synchronized
            else "Monero daemon synchronization is in progress."
        )

        progress = None
        if (
            isinstance(height, int)
            and isinstance(target_height, int)
            and target_height > 0
        ):
            progress = min(max(height / target_height, 0.0), 1.0)

        return {
            "healthy": True,
            "status": "online",
            "chain": "monero",
            "providerId": "monero-mainnet",
            "runtimeState": runtime_state,
            "runtimeStateReason": reason,
            "runtimeRpcReachable": True,
            "runtimeRpcHealthy": True,
            "height": height,
            "targetHeight": target_height,
            "verificationProgress": progress,
            "synchronized": synchronized,
            "peers": {
                "incoming": info.get("incoming_connections_count"),
                "outgoing": info.get("outgoing_connections_count"),
            },
            "nettype": info.get("nettype"),
            "version": info.get("version"),
            "databaseSizeBytes": info.get("database_size"),
            "storage": storage(),
            "measuredAt": time.time(),
        }
    except Exception as exc:
        return {
            "healthy": False,
            "status": "degraded",
            "chain": "monero",
            "providerId": "monero-mainnet",
            "runtimeState": "degraded",
            "runtimeStateReason": str(exc),
            "runtimeRpcReachable": False,
            "runtimeRpcHealthy": False,
            "error": str(exc),
            "storage": storage(),
            "measuredAt": time.time(),
        }


class Handler(BaseHTTPRequestHandler):
    def send_json(self, payload: dict) -> None:
        body = json.dumps(payload, indent=2).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path in {"/", "/api/status"}:
            self.send_json(status_payload())
            return
        if self.path == "/api/health":
            payload = status_payload()
            self.send_json({
                "healthy": payload["healthy"],
                "status": payload["status"],
                "runtimeState": payload["runtimeState"],
                "runtimeRpcReachable": payload["runtimeRpcReachable"],
                "storage": payload["storage"],
            })
            return
        self.send_error(404)

    def log_message(self, format: str, *args) -> None:
        return


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
