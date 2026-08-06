from __future__ import annotations

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
from urllib.parse import unquote


CATALOG_PATH = Path(
    os.environ.get(
        "PROVIDER_CATALOG_PATH",
        "/catalog/providers.v1.json",
    )
)
BCH_APP_ID = os.environ.get(
    "BCH_APP_ID",
    "seymour-bch-node",
)
WEB_ROOT = Path(__file__).resolve().parent


def load_catalog() -> dict:
    return json.loads(CATALOG_PATH.read_text())


def provider_payload(provider: dict) -> dict:
    payload = dict(provider)
    payload["installAction"] = None

    if provider["providerId"] == "bitcoin-cash-mainnet":
        payload["installAction"] = {
            "type": "umbrel-app",
            "appId": BCH_APP_ID,
            "available": True,
            "label": "Install Bitcoin Cash",
        }

    return payload


class Handler(BaseHTTPRequestHandler):
    server_version = "SeymourBlockchainManager/0.1"

    def send_json(
        self,
        payload: object,
        status: int = HTTPStatus.OK,
    ) -> None:
        body = json.dumps(
            payload,
            indent=2,
        ).encode()

        self.send_response(status)
        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8",
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
        if not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        body = path.read_bytes()

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header(
            "Content-Length",
            str(len(body)),
        )
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/api/health":
            catalog = load_catalog()
            self.send_json(
                {
                    "status": "ok",
                    "service": "seymour-blockchain-manager",
                    "catalogVersion": catalog[
                        "catalogVersion"
                    ],
                    "providerCount": len(
                        catalog["providers"]
                    ),
                }
            )
            return

        if self.path == "/api/providers":
            catalog = load_catalog()
            providers = [
                provider_payload(provider)
                for provider in catalog["providers"]
            ]

            self.send_json(
                {
                    "schemaVersion": catalog[
                        "schemaVersion"
                    ],
                    "catalogVersion": catalog[
                        "catalogVersion"
                    ],
                    "frozen": catalog["frozen"],
                    "providerCount": len(providers),
                    "providers": providers,
                }
            )
            return

        prefix = "/api/providers/"

        if self.path.startswith(prefix):
            provider_id = unquote(
                self.path[len(prefix):]
            )
            catalog = load_catalog()

            for provider in catalog["providers"]:
                if provider["providerId"] == provider_id:
                    self.send_json(
                        provider_payload(provider)
                    )
                    return

            self.send_json(
                {
                    "error": "provider-not-found",
                    "providerId": provider_id,
                },
                status=HTTPStatus.NOT_FOUND,
            )
            return

        if self.path in {"/", "/index.html"}:
            self.send_file(
                WEB_ROOT / "index.html",
                "text/html; charset=utf-8",
            )
            return

        if self.path == "/app.js":
            self.send_file(
                WEB_ROOT / "app.js",
                "application/javascript; charset=utf-8",
            )
            return

        if self.path == "/style.css":
            self.send_file(
                WEB_ROOT / "style.css",
                "text/css; charset=utf-8",
            )
            return

        self.send_error(HTTPStatus.NOT_FOUND)

    def log_message(
        self,
        format: str,
        *args: object,
    ) -> None:
        return


if __name__ == "__main__":
    server = ThreadingHTTPServer(
        ("0.0.0.0", 8080),
        Handler,
    )
    server.serve_forever()
