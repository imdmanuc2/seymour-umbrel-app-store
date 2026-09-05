from __future__ import annotations

import unittest

from shared.blockchain_install import (
    InstallRequest,
    InstallResult,
)


class SharedBlockchainInstallExecutionTests(
    unittest.TestCase
):
    def test_result_success_property(self):
        result = InstallResult(
            operation_id="operation-1",
            status="succeeded",
        )

        self.assertTrue(result.succeeded)

    def test_failed_result_is_not_successful(self):
        result = InstallResult(
            operation_id="operation-2",
            status="failed",
            error="preflight failed",
        )

        self.assertFalse(result.succeeded)
        self.assertEqual(
            result.error,
            "preflight failed",
        )

    def test_result_projection_is_provider_neutral(self):
        result = InstallResult(
            operation_id="operation-3",
            status="succeeded",
            result={"providerId": "bitcoin-mainnet"},
            verification={"verified": True},
        )

        payload = result.to_dict()

        self.assertEqual(
            payload["operationId"],
            "operation-3",
        )
        self.assertEqual(
            payload["status"],
            "succeeded",
        )
        self.assertNotIn(
            "docker",
            str(payload).lower(),
        )
        self.assertNotIn(
            "umbrel",
            str(payload).lower(),
        )

    def test_request_and_result_share_common_package(self):
        request = InstallRequest.from_dict(
            {
                "providerId": "bitcoin-mainnet",
                "appId": "seymour-bitcoin-node",
                "nodeName": "Bitcoin Node",
                "rpcUser": "seymour_rpc",
                "rpcPassword": "x" * 32,
                "rpcPort": 8332,
                "p2pPort": 8333,
                "storageTargetId": "storage-1",
                "confirmation":
                    "INSTALL-seymour-bitcoin-node",
            }
        )

        self.assertEqual(
            request.__class__.__module__,
            "shared.blockchain_install.request",
        )


if __name__ == "__main__":
    unittest.main()
