from __future__ import annotations

import unittest
from pathlib import Path

from shared.blockchain_install.request_materializer import (
    materialize_install_request,
)


ROOT = Path(__file__).resolve().parents[1]
CATALOG = (
    ROOT
    / "shared"
    / "provider_catalog"
    / "providers.v1.json"
)


class SharedInstallRequestMaterializerTests(
    unittest.TestCase
):
    def test_bitcoin_materializes_canonical_contract(
        self,
    ):
        calls = []

        def credentials():
            calls.append(True)
            return (
                "seymour_rpc",
                "a" * 32,
            )

        request = materialize_install_request(
            provider_id="bitcoin-mainnet",
            storage_target_id="storage-1",
            catalog_path=CATALOG,
            credential_generator=credentials,
        )

        self.assertEqual(
            request.provider_id,
            "bitcoin-mainnet",
        )
        self.assertEqual(
            request.app_id,
            "seymour-bitcoin-node",
        )
        self.assertEqual(
            request.node_name,
            "Seymour Bitcoin Node",
        )
        self.assertEqual(
            request.rpc_user,
            "seymour_rpc",
        )
        self.assertEqual(
            request.rpc_password,
            "a" * 32,
        )
        self.assertEqual(
            request.rpc_port,
            8332,
        )
        self.assertEqual(
            request.p2p_port,
            8333,
        )
        self.assertEqual(
            request.storage_target_id,
            "storage-1",
        )
        self.assertEqual(
            request.confirmation,
            "INSTALL-seymour-bitcoin-node",
        )
        self.assertEqual(calls, [True])

    def test_bitcoin_cash_materializes_canonical_contract(
        self,
    ):
        request = materialize_install_request(
            provider_id="bitcoin-cash-mainnet",
            storage_target_id="storage-bch",
            catalog_path=CATALOG,
            credential_generator=lambda: (
                "seymour_rpc",
                "b" * 32,
            ),
        )

        self.assertEqual(
            request.app_id,
            "seymour-bch-node",
        )
        self.assertEqual(
            request.node_name,
            "Seymour Bitcoin Cash Node",
        )
        self.assertEqual(
            request.rpc_port,
            8332,
        )
        self.assertEqual(
            request.p2p_port,
            8333,
        )
        self.assertEqual(
            request.confirmation,
            "INSTALL-seymour-bch-node",
        )

    def test_monero_does_not_generate_credentials(
        self,
    ):
        calls = []

        def credentials():
            calls.append(True)
            raise AssertionError(
                "credential generator must not run"
            )

        request = materialize_install_request(
            provider_id="monero-mainnet",
            storage_target_id="storage-xmr",
            catalog_path=CATALOG,
            credential_generator=credentials,
        )

        self.assertEqual(calls, [])
        self.assertEqual(
            request.app_id,
            "seymour-monero-node",
        )
        self.assertEqual(
            request.node_name,
            "Seymour Monero Node",
        )
        self.assertEqual(
            request.rpc_user,
            "",
        )
        self.assertEqual(
            request.rpc_password,
            "",
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

    def test_custom_node_name_is_preserved(
        self,
    ):
        request = materialize_install_request(
            provider_id="bitcoin-mainnet",
            storage_target_id="storage-1",
            catalog_path=CATALOG,
            node_name="Basement Bitcoin Node",
            credential_generator=lambda: (
                "seymour_rpc",
                "c" * 32,
            ),
        )

        self.assertEqual(
            request.node_name,
            "Basement Bitcoin Node",
        )

    def test_blank_node_name_uses_default(
        self,
    ):
        request = materialize_install_request(
            provider_id="monero-mainnet",
            storage_target_id="storage-1",
            catalog_path=CATALOG,
            node_name="   ",
        )

        self.assertEqual(
            request.node_name,
            "Seymour Monero Node",
        )

    def test_unknown_provider_fails_closed(
        self,
    ):
        with self.assertRaisesRegex(
            ValueError,
            "Unknown blockchain provider",
        ):
            materialize_install_request(
                provider_id="unknown-mainnet",
                storage_target_id="storage-1",
                catalog_path=CATALOG,
            )

    def test_missing_storage_target_fails_closed(
        self,
    ):
        with self.assertRaisesRegex(
            ValueError,
            "Storage target is required",
        ):
            materialize_install_request(
                provider_id="monero-mainnet",
                storage_target_id="",
                catalog_path=CATALOG,
            )

    def test_short_generated_password_fails_validation(
        self,
    ):
        with self.assertRaisesRegex(
            ValueError,
            "at least 24 characters",
        ):
            materialize_install_request(
                provider_id="bitcoin-mainnet",
                storage_target_id="storage-1",
                catalog_path=CATALOG,
                credential_generator=lambda: (
                    "seymour_rpc",
                    "short",
                ),
            )

    def test_empty_generated_user_fails_validation(
        self,
    ):
        with self.assertRaisesRegex(
            ValueError,
            "RPC user is required",
        ):
            materialize_install_request(
                provider_id="bitcoin-mainnet",
                storage_target_id="storage-1",
                catalog_path=CATALOG,
                credential_generator=lambda: (
                    "",
                    "d" * 32,
                ),
            )


if __name__ == "__main__":
    unittest.main()
