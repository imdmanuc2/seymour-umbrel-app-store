from __future__ import annotations

import base64
import json
import os
import shutil
import urllib.request
from http.server import (
    BaseHTTPRequestHandler,
    ThreadingHTTPServer,
)
from pathlib import Path
from urllib.parse import parse_qs

from provisioning import (
    build_plan,
    ensure_rpc_secrets,
    load_plan,
    save_plan,
)


RPC_HOST = os.getenv(
    "BCH_RPC_HOST",
    "node",
)
RPC_PORT = int(
    os.getenv(
        "BCH_RPC_PORT",
        "8332",
    )
)
RPC_USER = os.getenv(
    "BCH_RPC_USER",
    "seymour_rpc",
)
RPC_PASSWORD = os.getenv(
    "BCH_RPC_PASSWORD",
    "change-me-before-production",
)

DATA_PATH = Path(
    os.environ.get(
        "BCH_DATA_PATH",
        "/node-data",
    )
)


def rpc_call(
    method: str,
    timeout: int = 5,
) -> dict:
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
        timeout=timeout,
    ) as response:
        result = json.loads(
            response.read()
        )

    if result.get("error"):
        raise RuntimeError(
            str(result["error"])
        )

    return result["result"]


def storage_payload() -> dict:
    try:
        usage = shutil.disk_usage(
            DATA_PATH
        )
        return {
            "path": str(DATA_PATH),
            "totalBytes": usage.total,
            "usedBytes": usage.used,
            "freeBytes": usage.free,
            "healthy": True,
        }
    except Exception as exc:
        return {
            "path": str(DATA_PATH),
            "healthy": False,
            "error": str(exc),
        }


def status_payload() -> dict:
    # Lightweight RPC liveness check.
    #
    # getblockchaininfo can take a long time while BCHN is
    # performing initial block download, so it must not decide
    # whether the node itself is reachable.
    try:
        uptime = rpc_call(
            "uptime",
            timeout=5,
        )
    except Exception as exc:
        return {
            "healthy": False,
            "status": "starting",
            "chain": "bitcoin-cash",
            "rpcReachable": False,
            "rpcHealthy": False,
            "error": str(exc),
            "storage": storage_payload(),
        }

    # RPC is alive. Detailed chain telemetry is allowed more
    # time and may legitimately be slow during IBD.
    try:
        blockchain = rpc_call(
            "getblockchaininfo",
            timeout=20,
        )

        network = rpc_call(
            "getnetworkinfo",
            timeout=20,
        )

    except Exception as exc:
        return {
            "healthy": True,
            "status": "rpc-slow",
            "chain": "bitcoin-cash",
            "rpcReachable": True,
            "rpcHealthy": True,
            "uptime": uptime,
            "warning": "Detailed blockchain telemetry is temporarily slow.",
            "error": str(exc),
            "storage": storage_payload(),
        }

    return {
        "healthy": True,
        "status": "online",
        "chain": "bitcoin-cash",
        "rpcReachable": True,
        "rpcHealthy": True,
        "uptime": uptime,
        "blocks": blockchain.get(
            "blocks"
        ),
        "headers": blockchain.get(
            "headers"
        ),
        "verificationProgress": (
            blockchain.get(
                "verificationprogress"
            )
        ),
        "initialBlockDownload": (
            blockchain.get(
                "initialblockdownload"
            )
        ),
        "peers": network.get(
            "connections"
        ),
        "subversion": network.get(
            "subversion"
        ),
        "storage": storage_payload(),
    }


def health_payload() -> dict:
    """
    Fast BCH RPC liveness endpoint.

    Detailed blockchain state is intentionally excluded because
    getblockchaininfo may be slow during initial block download.
    """
    try:
        uptime = rpc_call(
            "uptime",
            timeout=5,
        )

        return {
            "healthy": True,
            "status": "online",
            "chain": "bitcoin-cash",
            "rpcReachable": True,
            "rpcHealthy": True,
            "uptime": uptime,
            "storage": storage_payload(),
        }

    except Exception as exc:
        return {
            "healthy": False,
            "status": "starting",
            "chain": "bitcoin-cash",
            "rpcReachable": False,
            "rpcHealthy": False,
            "error": str(exc),
            "storage": storage_payload(),
        }


def readiness_payload() -> dict:
    status = status_payload()
    plan = load_plan()

    ready = (
        status.get("healthy") is True
        and status.get(
            "initialBlockDownload"
        )
        is False
    )

    return {
        "ready": ready,
        "status": status,
        "provisioningPlan": plan,
    }


class Handler(BaseHTTPRequestHandler):
    def send_json(
        self,
        payload: dict,
        status_code: int = 200,
    ) -> None:
        body = json.dumps(
            payload,
            indent=2,
        ).encode()

        self.send_response(
            status_code
        )
        self.send_header(
            "Content-Type",
            "application/json",
        )
        self.send_header(
            "Content-Length",
            str(len(body)),
        )
        self.end_headers()
        try:
            self.wfile.write(body)
        except (
            BrokenPipeError,
            ConnectionResetError,
        ):
            return

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

    def read_form(
        self,
    ) -> dict[str, str]:
        length = int(
            self.headers.get(
                "Content-Length",
                "0",
            )
        )
        body = self.rfile.read(
            length
        ).decode()
        parsed = parse_qs(body)

        return {
            key: values[-1]
            for key, values in parsed.items()
        }

    def do_GET(self) -> None:
        if self.path == "/":
            self.send_file(
                Path(
                    "/app/index.html"
                ),
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
            self.send_json(
                status_payload()
            )
            return

        if self.path == "/api/health":
            payload = health_payload()
            self.send_json(
                payload,
                200
                if payload["healthy"]
                else 503,
            )
            return

        if self.path == "/api/readiness":
            payload = readiness_payload()
            self.send_json(
                payload,
                200
                if payload["ready"]
                else 503,
            )
            return

        if self.path == "/api/storage":
            self.send_json(
                storage_payload()
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
                        "/provisioning/"
                        "modes.json"
                    ).read_text()
                )
            )
            return

        if self.path == "/api/provisioning/status":
            self.send_json(
                {
                    "plan": load_plan(),
                    "secretsReady": (
                        Path(
                            "/state/"
                            "rpc-secrets.json"
                        ).exists()
                    ),
                }
            )
            return

        self.send_json(
            {
                "error": "Not found",
            },
            404,
        )

    def do_POST(self) -> None:
        if self.path == "/api/provisioning/plan":
            plan = build_plan(
                self.read_form()
            )
            self.send_json(
                plan,
                200
                if plan["validation"]["valid"]
                else 400,
            )
            return

        if self.path == "/api/provisioning/apply":
            plan = build_plan(
                self.read_form()
            )

            if (
                not plan["validation"]["valid"]
                or plan["mode"] != "fresh-sync"
            ):
                self.send_json(
                    {
                        "applied": False,
                        "plan": plan,
                        "error": (
                            "Only a valid fresh-sync plan "
                            "can be applied in SBP-003."
                        ),
                    },
                    400,
                )
                return

            save_plan(plan)
            secrets = ensure_rpc_secrets()

            self.send_json(
                {
                    "applied": True,
                    "plan": plan,
                    "rpcUser": secrets["rpcUser"],
                    "rpcPasswordGenerated": True,
                    "nextStep": (
                        "Install or restart the Umbrel app "
                        "to begin synchronization."
                    ),
                }
            )
            return

        self.send_json(
            {
                "error": "Not found",
            },
            404,
        )

    def log_message(
        self,
        format: str,
        *args,
    ) -> None:
        return


if __name__ == "__main__":
    ThreadingHTTPServer(
        (
            "0.0.0.0",
            8080,
        ),
        Handler,
    ).serve_forever()
