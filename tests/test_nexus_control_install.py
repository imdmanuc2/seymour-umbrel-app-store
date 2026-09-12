from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from seymour_test_support import load_nexus_control


ROOT = Path(__file__).resolve().parents[1]
CATALOG = (
    ROOT
    / "shared"
    / "provider_catalog"
    / "providers.v1.json"
)


@dataclass
class FakeResult:
    operation_id: str = "operation-test"
    status: str = "succeeded"

    def to_dict(self):
        return {
            "operationId": self.operation_id,
            "status": self.status,
            "result": {
                "providerId": "bitcoin-mainnet",
            },
            "verification": {
                "verified": True,
            },
            "error": None,
        }


class FakeInstaller:
    def __init__(self):
        self.requests = []

    def execute_shared(self, request):
        self.requests.append(request)
        return FakeResult()


class NexusControlInstallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_nexus_control()

    def test_fails_closed_without_control_token(self):
        with patch.dict(
            os.environ,
            {},
            clear=True,
        ):
            allowed, payload, status = (
                self.module.authorize({})
            )

        self.assertFalse(allowed)
        self.assertEqual(
            status,
            HTTPStatus.SERVICE_UNAVAILABLE,
        )
        self.assertEqual(
            payload["error"],
            "nexus-control-not-configured",
        )

    def test_requires_bearer_authentication(self):
        with patch.dict(
            os.environ,
            {
                "NEXUS_CONTROL_TOKEN":
                    "target-secret-value",
            },
            clear=False,
        ):
            allowed, payload, status = (
                self.module.authorize({})
            )

        self.assertFalse(allowed)
        self.assertEqual(
            status,
            HTTPStatus.UNAUTHORIZED,
        )
        self.assertNotIn(
            "target-secret-value",
            str(payload),
        )

    def test_rejects_wrong_bearer_token(self):
        with patch.dict(
            os.environ,
            {
                "NEXUS_CONTROL_TOKEN":
                    "target-secret-value",
            },
            clear=False,
        ):
            allowed, payload, status = (
                self.module.authorize({
                    "Authorization":
                        "Bearer wrong-value",
                })
            )

        self.assertFalse(allowed)
        self.assertEqual(
            status,
            HTTPStatus.FORBIDDEN,
        )
        self.assertNotIn(
            "target-secret-value",
            str(payload),
        )

    def test_accepts_exact_bearer_token(self):
        with patch.dict(
            os.environ,
            {
                "NEXUS_CONTROL_TOKEN":
                    "target-secret-value",
            },
            clear=False,
        ):
            allowed, payload, status = (
                self.module.authorize({
                    "Authorization":
                        "Bearer target-secret-value",
                })
            )

        self.assertTrue(allowed)
        self.assertIsNone(payload)
        self.assertEqual(
            status,
            HTTPStatus.OK,
        )

    def test_rejects_caller_controlled_fields(self):
        with patch.object(
            self.module,
            "CATALOG_PATH",
            CATALOG,
        ):
            with self.assertRaisesRegex(
                ValueError,
                "Unsupported Nexus install parameters",
            ):
                self.module.materialize_remote_install_request({
                    "providerId":
                        "bitcoin-mainnet",
                    "storageTargetId":
                        "storage-1",
                    "rpcPassword":
                        "caller-secret",
                })

    def test_materializes_identity_and_secrets_on_target(self):
        with patch.object(
            self.module,
            "CATALOG_PATH",
            CATALOG,
        ):
            request = (
                self.module
                .materialize_remote_install_request({
                    "providerId":
                        "monero-mainnet",
                    "storageTargetId":
                        "storage-xmr",
                })
            )

        self.assertEqual(
            request.provider_id,
            "monero-mainnet",
        )
        self.assertEqual(
            request.app_id,
            "seymour-monero-node",
        )
        self.assertEqual(
            request.rpc_port,
            18081,
        )
        self.assertEqual(
            request.p2p_port,
            18080,
        )
        self.assertEqual(
            request.confirmation,
            "INSTALL-seymour-monero-node",
        )

    def test_executes_through_shared_manager_surface(self):
        installer = FakeInstaller()

        with patch.object(
            self.module,
            "CATALOG_PATH",
            CATALOG,
        ):
            payload, status = (
                self.module.execute_install(
                    {
                        "providerId":
                            "monero-mainnet",
                        "storageTargetId":
                            "storage-xmr",
                    },
                    installer,
                )
            )

        self.assertEqual(
            status,
            HTTPStatus.OK,
        )
        self.assertEqual(
            payload["status"],
            "succeeded",
        )
        self.assertEqual(
            len(installer.requests),
            1,
        )


if __name__ == "__main__":
    unittest.main()
