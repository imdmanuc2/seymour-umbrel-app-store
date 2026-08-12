from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import base64
import json
import os
from pathlib import Path
import urllib.error
import urllib.request


RPC_HOST = os.environ.get("BTC_RPC_HOST", "node")
RPC_PORT = int(os.environ.get("BTC_RPC_PORT", "8332"))
RPC_USER = os.environ.get("BTC_RPC_USER", "seymour_rpc")
RPC_PASSWORD = os.environ.get(
    "BTC_RPC_PASSWORD",
    "change-me-before-production",
)
DATA_PATH = Path(os.environ.get("BTC_DATA_PATH", "/node-data"))


def rpc(method: str) -> dict:
    payload = json.dumps({
        "jsonrpc": "1.0",
        "id": "seymour",
        "method": method,
        "params": [],
    }).encode()

    request = urllib.request.Request(
        f"http://{RPC_HOST}:{RPC_PORT}/",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Basic " + base64.b64encode(
                f"{RPC_USER}:{RPC_PASSWORD}".encode()
            ).decode(),
        },
    )

    with urllib.request.urlopen(request, timeout=10) as response:
        body = json.loads(response.read().decode())

    if body.get("error"):
        raise RuntimeError(str(body["error"]))

    return body.get("result")


def storage() -> dict:
    stat = os.statvfs(DATA_PATH)
    total = stat.f_blocks * stat.f_frsize
    free = stat.f_bavail * stat.f_frsize

    return {
        "path": str(DATA_PATH),
        "totalBytes": total,
        "usedBytes": total - free,
        "freeBytes": free,
        "healthy": True,
    }


def status_payload() -> dict:
    try:
        chain = rpc("getblockchaininfo")
        network = rpc("getnetworkinfo")

        return {
            "healthy": True,
            "status": "online",
            "chain": "bitcoin",
            "runtimeState": (
                "syncing"
                if chain.get("initialblockdownload")
                else "running"
            ),
            "runtimeStateReason": (
                "Bitcoin Core initial block download is active."
                if chain.get("initialblockdownload")
                else "Bitcoin Core RPC is healthy."
            ),
            "runtimeRpcReachable": True,
            "runtimeRpcHealthy": True,
            "runtimeInitialBlockDownload":
                chain.get("initialblockdownload"),
            "runtimeVerificationProgress":
                chain.get("verificationprogress"),
            "blocks": chain.get("blocks"),
            "headers": chain.get("headers"),
            "verificationProgress":
                chain.get("verificationprogress"),
            "initialBlockDownload":
                chain.get("initialblockdownload"),
            "peers": network.get("connections"),
            "subversion": network.get("subversion"),
            "storage": storage(),
        }

    except Exception as exc:
        return {
            "healthy": False,
            "status": "degraded",
            "chain": "bitcoin",
            "runtimeState": "degraded",
            "runtimeStateReason": str(exc),
            "runtimeRpcReachable": False,
            "runtimeRpcHealthy": False,
            "error": str(exc),
            "storage": storage(),
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
                "chain": payload["chain"],
                "runtimeState": payload["runtimeState"],
                "runtimeRpcReachable":
                    payload["runtimeRpcReachable"],
                "storage": payload["storage"],
            })
            return

        self.send_error(404)

    def log_message(self, format: str, *args: object) -> None:
        return


ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
