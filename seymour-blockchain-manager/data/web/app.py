from __future__ import annotations

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
from urllib.parse import unquote

from telemetry import dashboard_payload
from sync_manager import analyze
from operations_center import OperationKind, diagnostics, execute_backup, plan, recent_logs, recommendations
from lifecycle import GuardedLifecycleService, LifecycleAction


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
LIFECYCLE = GuardedLifecycleService()
INSTALLER = Installer()
ADOPTION = AdoptionService()


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
            "confirmation": f"INSTALL-{BCH_APP_ID}",
        }

    return payload


class Handler(BaseHTTPRequestHandler):
    server_version = "SeymourBlockchainManager/0.2"

    def send_json(
        self,
        payload: object,
        status: int = HTTPStatus.OK,
    ) -> None:
        body = json.dumps(payload, indent=2).encode()
        self.send_response(status)
        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8",
        )
        self.send_header(
            "Cache-Control",
            "no-store",
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
        if self.path.startswith("/api/adoption/plans/"):
            operation_id = self.path.rsplit("/", 1)[-1]
            try:
                self.send_json(ADOPTION.load(operation_id))
            except KeyError:
                self.send_json({"error": "adoption-plan-not-found"}, status=HTTPStatus.NOT_FOUND)
            return

        if self.path == "/api/install/preflight":
            self.send_json(preflight())
            return

        if self.path == "/api/install/credentials":
            self.send_json(generate_credentials())
            return

        if self.path == "/api/health":
            catalog = load_catalog()
            self.send_json({
                "status": "ok",
                "service": "seymour-blockchain-manager",
                "catalogVersion": catalog["catalogVersion"],
                "providerCount": len(catalog["providers"]),
            })
            return

        if self.path == "/api/dashboard":
            self.send_json(dashboard_payload())
            return

        if self.path == "/api/nexus/delivery/status":
            self.send_json(load_status())
            return

        if self.path == "/api/nexus/discovery":
            dashboard = dashboard_payload()
            sync = analyze(dashboard)
            self.send_json(discovery_document(dashboard, sync))
            return

        if self.path == "/api/nexus/registration":
            dashboard = dashboard_payload()
            sync = analyze(dashboard)
            payload = registration_payload(dashboard, sync)
            append_registration_evidence(payload)
            self.send_json(payload)
            return

        if self.path == "/api/operations/diagnostics":
            result = diagnostics()
            payload = result.to_dict()
            payload["recommendations"] = recommendations(result.result or {})
            self.send_json(payload)
            return

        if self.path.startswith("/api/operations/logs"):
            self.send_json(recent_logs().to_dict())
            return

        if self.path == "/api/sync":
            self.send_json(analyze(dashboard_payload()))
            return

        if self.path == "/api/providers":
            catalog = load_catalog()
            providers = [
                provider_payload(provider)
                for provider in catalog["providers"]
            ]
            self.send_json({
                "schemaVersion": catalog["schemaVersion"],
                "catalogVersion": catalog["catalogVersion"],
                "frozen": catalog["frozen"],
                "providerCount": len(providers),
                "providers": providers,
            })
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

        files = {
            "/": ("index.html", "text/html; charset=utf-8"),
            "/index.html": ("index.html", "text/html; charset=utf-8"),
            "/app.js": ("app.js", "application/javascript; charset=utf-8"),
            "/style.css": ("style.css", "text/css; charset=utf-8"),
        }

        if self.path in files:
            name, content_type = files[self.path]
            self.send_file(
                WEB_ROOT / name,
                content_type,
            )
            return

        self.send_error(HTTPStatus.NOT_FOUND)


    def do_POST(self) -> None:
        if self.path == "/api/nexus/delivery":
            body = self.read_json_body()

            dashboard = dashboard_payload()
            sync = analyze(dashboard)

            payload = registration_payload(
                dashboard,
                sync,
            )

            result = deliver(
                payload,
                dry_run=bool(
                    body.get(
                        "dryRun",
                        False,
                    )
                ),
            )

            status = (
                HTTPStatus.OK
                if result.status in {
                    "succeeded",
                    "dry-run",
                }
                else HTTPStatus.BAD_GATEWAY
            )

            self.send_json(
                result.to_dict(),
                status=status,
            )
            return

        if self.path == "/api/operations/plan":
            body = self.read_json_body()
            self.send_json(plan(OperationKind(str(body.get("kind", ""))), dict(body.get("details", {}))).to_dict())
            return

        if self.path == "/api/operations/backup":
            body = self.read_json_body()
            result = execute_backup(str(body.get("confirmation", "")))
            status = HTTPStatus.OK if result.status.value == "succeeded" else HTTPStatus.BAD_REQUEST
            self.send_json(result.to_dict(), status=status)
            return

        if self.path == "/api/adoption/plan":
            body = self.read_json_body()
            self.send_json(ADOPTION.plan(Path(str(body.get("sourcePath", "")))).to_dict())
            return

        if self.path == "/api/adoption/execute":
            body = self.read_json_body()
            result = ADOPTION.execute(str(body.get("operationId", "")), str(body.get("confirmation", "")))
            status = HTTPStatus.OK if result.status.value == "succeeded" else HTTPStatus.BAD_REQUEST
            self.send_json(result.to_dict(), status=status)
            return

        if self.path == "/api/install/execute":
            try:
                operation = INSTALLER.execute(InstallRequest.from_dict(self.read_json_body()))
                status = HTTPStatus.OK if operation.status.value == "succeeded" else HTTPStatus.BAD_REQUEST
                self.send_json(operation.to_dict(), status=status)
            except ValueError as exc:
                self.send_json({"error": "invalid-install-request", "message": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            except Exception as exc:
                self.send_json({"error": "installation-failure", "message": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        prefix = "/api/lifecycle/"
        if not self.path.startswith(prefix):
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        action = LifecycleAction(self.path[len(prefix):])
        length = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(length).decode()) if length else {}
        result = LIFECYCLE.execute(
            provider_id=str(body.get("providerId", "")),
            app_id=str(body.get("appId", "")),
            action=action,
            confirmation=body.get("confirmation"),
        )
        self.send_json(result.to_dict(), status=HTTPStatus.OK if result.status.value == "succeeded" else HTTPStatus.BAD_REQUEST)

    def log_message(
        self,
        format: str,
        *args: object,
    ) -> None:
        return


if __name__ == "__main__":
    ThreadingHTTPServer(
        ("0.0.0.0", 8080),
        Handler,
    ).serve_forever()
