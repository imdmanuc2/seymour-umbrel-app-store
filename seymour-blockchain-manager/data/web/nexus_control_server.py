from __future__ import annotations

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import ssl
from typing import Any

from installer import Installer
from nexus_control import (
    authorize,
    execute_install,
)


DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8571
DEFAULT_TLS_CERTFILE = "/tls/server.crt"
DEFAULT_TLS_KEYFILE = "/tls/server.key"
INSTALL_PATH = "/api/nexus/install/execute"

INSTALLER = Installer()


def _host() -> str:
    value = str(
        os.environ.get(
            "NEXUS_CONTROL_HTTP_HOST",
            DEFAULT_HOST,
        )
    ).strip()

    return value or DEFAULT_HOST


def _port() -> int:
    raw = str(
        os.environ.get(
            "NEXUS_CONTROL_HTTP_PORT",
            DEFAULT_PORT,
        )
    ).strip()

    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(
            "NEXUS_CONTROL_HTTP_PORT must be an integer."
        ) from exc

    if not 1 <= value <= 65535:
        raise ValueError(
            "NEXUS_CONTROL_HTTP_PORT must be between 1 and 65535."
        )

    return value


def _tls_file(
    environment_name: str,
    default_path: str,
) -> Path:
    value = str(
        os.environ.get(
            environment_name,
            default_path,
        )
    ).strip()

    if not value:
        raise ValueError(
            f"{environment_name} is required."
        )

    path = Path(
        value
    )

    if not path.is_absolute():
        raise ValueError(
            f"{environment_name} must be an absolute path."
        )

    if not path.is_file():
        raise ValueError(
            f"{environment_name} does not reference a file."
        )

    return path


def _tls_context() -> ssl.SSLContext:
    certfile = _tls_file(
        "NEXUS_CONTROL_TLS_CERTFILE",
        DEFAULT_TLS_CERTFILE,
    )

    keyfile = _tls_file(
        "NEXUS_CONTROL_TLS_KEYFILE",
        DEFAULT_TLS_KEYFILE,
    )

    context = ssl.SSLContext(
        ssl.PROTOCOL_TLS_SERVER
    )

    context.minimum_version = (
        ssl.TLSVersion.TLSv1_2
    )

    try:
        context.load_cert_chain(
            certfile=str(certfile),
            keyfile=str(keyfile),
        )
    except (
        OSError,
        ssl.SSLError,
    ) as exc:
        raise ValueError(
            "Nexus control TLS certificate/key "
            "could not be loaded."
        ) from exc

    return context


class NexusControlHandler(BaseHTTPRequestHandler):
    server_version = "SeymourNexusControl/1"

    def _send_json(
        self,
        payload: dict[str, Any],
        *,
        status: int,
    ) -> None:
        body = json.dumps(
            payload,
            separators=(",", ":"),
        ).encode("utf-8")

        self.send_response(status)
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

    def _not_found(self) -> None:
        self._send_json(
            {
                "contract": "seymour.nexus-control-error",
                "version": 1,
                "error": "not-found",
                "message": "Control route not found.",
            },
            status=HTTPStatus.NOT_FOUND,
        )

    def _read_json_body(self) -> dict[str, Any]:
        raw_length = str(
            self.headers.get(
                "Content-Length",
                "0",
            )
        ).strip()

        try:
            length = int(raw_length)
        except ValueError as exc:
            raise ValueError(
                "Content-Length is invalid."
            ) from exc

        if length <= 0:
            raise ValueError(
                "JSON request body is required."
            )

        # The Nexus control contract contains only providerId and
        # storageTargetId. Reject unexpectedly large request bodies.
        if length > 16384:
            raise ValueError(
                "JSON request body is too large."
            )

        raw = self.rfile.read(length)

        try:
            payload = json.loads(
                raw.decode("utf-8")
            )
        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as exc:
            raise ValueError(
                "Request body must contain valid JSON."
            ) from exc

        if not isinstance(payload, dict):
            raise ValueError(
                "Nexus install request must be an object."
            )

        return payload

    def do_GET(self) -> None:
        self._not_found()

    def do_POST(self) -> None:
        if self.path != INSTALL_PATH:
            self._not_found()
            return

        authorized, auth_payload, auth_status = (
            authorize(self.headers)
        )

        if not authorized:
            self._send_json(
                auth_payload or {
                    "contract": "seymour.nexus-control-error",
                    "version": 1,
                    "error": "authentication-failure",
                    "message": "Nexus control authentication failed.",
                },
                status=auth_status,
            )
            return

        try:
            body = self._read_json_body()

            payload, status = execute_install(
                body,
                INSTALLER,
            )

            self._send_json(
                payload,
                status=status,
            )

        except (ValueError, TypeError) as exc:
            self._send_json(
                {
                    "contract": "seymour.nexus-control-error",
                    "version": 1,
                    "error": "invalid-install-request",
                    "message": str(exc),
                },
                status=HTTPStatus.BAD_REQUEST,
            )

        except Exception:
            self._send_json(
                {
                    "contract": "seymour.nexus-control-error",
                    "version": 1,
                    "error": "installation-failure",
                    "message": (
                        "Blockchain installation execution failed."
                    ),
                },
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def do_PUT(self) -> None:
        self._not_found()

    def do_PATCH(self) -> None:
        self._not_found()

    def do_DELETE(self) -> None:
        self._not_found()

    def log_message(
        self,
        format: str,
        *args: object,
    ) -> None:
        return


def main() -> None:
    tls_context = _tls_context()

    server = ThreadingHTTPServer(
        (_host(), _port()),
        NexusControlHandler,
    )

    try:
        server.socket = tls_context.wrap_socket(
            server.socket,
            server_side=True,
        )

        server.serve_forever()

    finally:
        server.server_close()


if __name__ == "__main__":
    main()
