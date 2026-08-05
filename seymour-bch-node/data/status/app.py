from __future__ import annotations

import base64
import json
import os
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

from provisioning import build_plan


RPC_HOST = os.getenv("BCH_RPC_HOST", "node")
RPC_PORT = int(os.getenv("BCH_RPC_PORT", "8332"))
RPC_USER = os.getenv("BCH_RPC_USER", "seymour_rpc")
RPC_PASSWORD = os.getenv(
    "BCH_RPC_PASSWORD",
    "change-me-before-production",
)


def rpc_call(method: str) -> dict:
    payload = json.dumps(
        {
            "jsonrpc": "1.0",
            "id": "seymour-status",
            "method": method,
            "params": [],
        }
    ).encode()

    token = base64.b64encode(
        f"{RPC_USER}:{RPC_PASSWORD}".encode()
    ).decode()

    request = urllib.request.Request(
        f"http://{RPC_HOST}:{RPC_PORT}",
        data=payload,
        headers={
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(
        request,
        timeout=5,
    ) as response:
        result = json.loads(response.read())

    if result.get("error"):
        raise RuntimeError(str(result["error"]))

    return result["result"]


def status_payload() -> dict:
    try:
        blockchain = rpc_call("getblockchaininfo")
        network = rpc_call("getnetworkinfo")

        return {
            "healthy": True,
            "status": "online",
            "chain": "bitcoin-cash",
            "blocks": blockchain.get("blocks"),
            "headers": blockchain.get("headers"),
            "verificationProgress": blockchain.get(
                "verificationprogress"
            ),
            "initialBlockDownload": blockchain.get(
                "initialblockdownload"
            ),
            "peers": network.get("connections"),
            "subversion": network.get("subversion"),
        }

    except Exception as exc:
        return {
            "healthy": False,
            "status": "starting",
            "chain": "bitcoin-cash",
            "error": str(exc),
        }


class Handler(BaseHTTPRequestHandler):
    def send_json(
        self,
        payload: dict,
        status_code: int = 200,
    ) -> None:
        body = json.dumps(payload, indent=2).encode()

        self.send_response(status_code)
        self.send_header(
            "Content-Type",
            "application/json",
        )
        self.send_header(
            "Content-Length",
            str(len(body)),
        )
        self.end_headers()
        self.wfile.write(body)

    def send_file(
        self,
        path: Path,
        content_type: str,
    ) -> None:
        body = path.read_bytes()

        self.send_response(200)
        self.send_header(
            "Content-Type",
            content_type,
        )
        self.send_header(
            "Content-Length",
            str(len(body)),
        )
        self.end_headers()
        self.wfile.write(body)

    def read_form(self) -> dict[str, str]:
        length = int(
            self.headers.get(
                "Content-Length",
                "0",
            )
        )

        body = self.rfile.read(length).decode()
        parsed = parse_qs(body)

        return {
            key: values[-1]
            for key, values in parsed.items()
        }

    def do_GET(self) -> None:
        if self.path == "/":
            self.send_file(
                Path("/app/index.html"),
                "text/html; charset=utf-8",
            )
            return

        if self.path == "/provision":
            self.send_file(
                Path(
                    "/app/templates/provision.html"
                ),
                "text/html; charset=utf-8",
            )
            return

        if self.path == "/api/status":
            self.send_json(status_payload())
            return

        if self.path == "/api/health":
            payload = status_payload()
            self.send_json(
                payload,
                200 if payload["healthy"] else 503,
            )
            return

        if self.path == "/api/contract":
            self.send_json(
                json.loads(
                    Path(
                        "/contracts/"
                        "bitcoin-cash-node.json"
                    ).read_text()
                )
            )
            return

        if self.path == "/api/provisioning":
            self.send_json(
                json.loads(
                    Path(
                        "/provisioning/modes.json"
                    ).read_text()
                )
            )
            return

        self.send_json(
            {"error": "Not found"},
            404,
        )

    def do_POST(self) -> None:
        if self.path != "/api/provisioning/plan":
            self.send_json(
                {"error": "Not found"},
                404,
            )
            return

        plan = build_plan(
            self.read_form()
        )

        self.send_json(
            plan,
            200
            if plan["validation"]["valid"]
            else 400,
        )

    def log_message(
        self,
        format: str,
        *args,
    ) -> None:
        return


if __name__ == "__main__":
    ThreadingHTTPServer(
        ("0.0.0.0", 8080),
        Handler,
    ).serve_forever()
