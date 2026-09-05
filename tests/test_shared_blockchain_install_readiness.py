from __future__ import annotations

import unittest

from shared.blockchain_install import (
    evaluate_provider_readiness,
)


class SharedProviderReadinessTests(
    unittest.TestCase
):
    def test_live_provider_is_ready(self):
        result = evaluate_provider_readiness({
            "providerId": "bitcoin-mainnet",
            "selectable": True,
            "productionImage": "example/image:1",
            "runtime": {
                "appId": "example",
            },
        })

        self.assertTrue(result["compatible"])
        self.assertEqual(result["errors"], [])

    def test_nonselectable_provider_fails(self):
        result = evaluate_provider_readiness({
            "providerId": "litecoin-mainnet",
            "selectable": False,
            "productionImage": None,
            "runtime": None,
        })

        self.assertFalse(result["compatible"])
        self.assertFalse(
            result["checks"]["providerSelectable"]
        )
        self.assertFalse(
            result["checks"]["productionImagePresent"]
        )
        self.assertFalse(
            result["checks"]["runtimePresent"]
        )

    def test_provider_readiness_is_host_independent(self):
        result = evaluate_provider_readiness({
            "providerId": "bitcoin-mainnet",
            "selectable": True,
            "productionImage": "example/image:1",
            "runtime": {},
        })

        self.assertNotIn(
            "networkAvailable",
            result["checks"],
        )
        self.assertNotIn(
            "dockerAvailable",
            result["checks"],
        )
        self.assertNotIn(
            "umbrelAvailable",
            result["checks"],
        )
        self.assertNotIn(
            "storageWritable",
            result["checks"],
        )


if __name__ == "__main__":
    unittest.main()
