from __future__ import annotations

from http import HTTPStatus
from http.client import HTTPConnection
import json
import os
from pathlib import Path
import sys
from threading import Thread
import unittest
from unittest.mock import patch


APP_ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = APP_ROOT / "data" / "web"
SHARED_ROOT = APP_ROOT / "data"

for import_root in (
    WEB_ROOT,
    SHARED_ROOT,
):
    value = str(import_root)

    if value not in sys.path:
        sys.path.insert(
            0,
            value,
        )


import nexus_control_server as control_server


class NexusControlServerTests(unittest.TestCase):
    def setUp(self):
        self.server = control_server.ThreadingHTTPServer(
            ("127.0.0.1", 0),
            control_server.NexusControlHandler,
        )

        self.thread = Thread(
            target=self.server.serve_forever,
            daemon=True,
        )
        self.thread.start()

        self.port = self.server.server_address[1]

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def request(
        self,
        method,
        path,
        *,
        headers=None,
        body=None,
    ):
        connection = HTTPConnection(
            "127.0.0.1",
            self.port,
            timeout=5,
        )

        encoded = None

        if body is not None:
            encoded = json.dumps(body)

        connection.request(
            method,
            path,
            body=encoded,
            headers=headers or {},
        )

        response = connection.getresponse()
        payload = response.read().decode("utf-8")
        status = response.status
        connection.close()

        return status, payload

    def test_get_root_is_not_found(self):
        status, _ = self.request(
            "GET",
            "/",
        )

        self.assertEqual(
            status,
            HTTPStatus.NOT_FOUND,
        )

    def test_get_install_route_is_not_found(self):
        status, _ = self.request(
            "GET",
            control_server.INSTALL_PATH,
        )

        self.assertEqual(
            status,
            HTTPStatus.NOT_FOUND,
        )

    def test_unknown_post_is_not_found(self):
        status, _ = self.request(
            "POST",
            "/api/not-real",
            body={},
        )

        self.assertEqual(
            status,
            HTTPStatus.NOT_FOUND,
        )

    def test_unconfigured_token_fails_closed(self):
        with patch.dict(
            os.environ,
            {},
            clear=False,
        ):
            os.environ.pop(
                "NEXUS_CONTROL_TOKEN",
                None,
            )

            status, payload = self.request(
                "POST",
                control_server.INSTALL_PATH,
                body={
                    "providerId": "btc",
                    "storageTargetId": "probe-only",
                },
            )

        self.assertEqual(
            status,
            HTTPStatus.SERVICE_UNAVAILABLE,
        )

        self.assertIn(
            "nexus-control-not-configured",
            payload,
        )

    def test_missing_bearer_is_unauthorized(self):
        with patch.dict(
            os.environ,
            {
                "NEXUS_CONTROL_TOKEN": "expected-secret",
            },
        ):
            status, _ = self.request(
                "POST",
                control_server.INSTALL_PATH,
                body={
                    "providerId": "btc",
                    "storageTargetId": "probe-only",
                },
            )

        self.assertEqual(
            status,
            HTTPStatus.UNAUTHORIZED,
        )

    def test_wrong_bearer_is_forbidden(self):
        with patch.dict(
            os.environ,
            {
                "NEXUS_CONTROL_TOKEN": "expected-secret",
            },
        ):
            status, _ = self.request(
                "POST",
                control_server.INSTALL_PATH,
                headers={
                    "Authorization": "Bearer wrong-secret",
                },
                body={
                    "providerId": "btc",
                    "storageTargetId": "probe-only",
                },
            )

        self.assertEqual(
            status,
            HTTPStatus.FORBIDDEN,
        )

    def test_authorized_request_uses_shared_execution(self):
        with (
            patch.dict(
                os.environ,
                {
                    "NEXUS_CONTROL_TOKEN": "expected-secret",
                },
            ),
            patch.object(
                control_server,
                "execute_install",
                return_value=(
                    {
                        "status": "succeeded",
                        "verified": True,
                    },
                    HTTPStatus.OK,
                ),
            ) as execute,
        ):
            status, payload = self.request(
                "POST",
                control_server.INSTALL_PATH,
                headers={
                    "Authorization": (
                        "Bearer expected-secret"
                    ),
                },
                body={
                    "providerId": "btc",
                    "storageTargetId": "storage-1",
                },
            )

        self.assertEqual(
            status,
            HTTPStatus.OK,
        )

        decoded = json.loads(payload)

        self.assertEqual(
            decoded["status"],
            "succeeded",
        )

        execute.assert_called_once()

    def test_port_validation(self):
        with patch.dict(
            os.environ,
            {
                "NEXUS_CONTROL_HTTP_PORT": "0",
            },
        ):
            with self.assertRaises(ValueError):
                control_server._port()

        with patch.dict(
            os.environ,
            {
                "NEXUS_CONTROL_HTTP_PORT": "65536",
            },
        ):
            with self.assertRaises(ValueError):
                control_server._port()

        with patch.dict(
            os.environ,
            {
                "NEXUS_CONTROL_HTTP_PORT": "not-a-port",
            },
        ):
            with self.assertRaises(ValueError):
                control_server._port()


if __name__ == "__main__":
    unittest.main()
