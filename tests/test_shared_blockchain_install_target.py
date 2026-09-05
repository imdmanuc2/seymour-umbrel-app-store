from __future__ import annotations

import unittest

from shared.blockchain_install import (
    TargetInstallExecution,
    TargetInstallPreflight,
    TargetInstallVerification,
)


class SharedTargetInstallContractTests(
    unittest.TestCase
):
    def test_preflight_projection(self):
        value = TargetInstallPreflight(
            compatible=True,
            checks={"runtime": True},
        )

        self.assertEqual(
            value.to_dict(),
            {
                "compatible": True,
                "checks": {
                    "runtime": True,
                },
                "errors": [],
            },
        )

    def test_execution_projection(self):
        value = TargetInstallExecution(
            success=True,
            result={"native": True},
            evidence={"adapter": "fake"},
        )

        self.assertTrue(value.success)
        self.assertEqual(
            value.to_dict()["evidence"],
            {"adapter": "fake"},
        )

    def test_verification_projection(self):
        value = TargetInstallVerification(
            verified=True,
            evidence={"installed": True},
        )

        self.assertTrue(value.verified)
        self.assertIsNone(value.error)


if __name__ == "__main__":
    unittest.main()
