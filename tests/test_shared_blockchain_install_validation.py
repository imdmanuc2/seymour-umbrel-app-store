from __future__ import annotations

from pathlib import Path
import unittest

from shared.blockchain_install import (
    InstallRequest,
    validate_install_request,
)


CATALOG = (
    Path(__file__).resolve().parents[1]
    / "shared"
    / "provider_catalog"
    / "providers.v1.json"
)


def make_request(
    **overrides,
) -> InstallRequest:
    data = {
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

    data.update(overrides)

    return InstallRequest.from_dict(data)


class SharedInstallValidationTests(
    unittest.TestCase
):
    def test_valid_bitcoin_request(self):
        validate_install_request(
            make_request(),
            CATALOG,
        )

    def test_app_id_mismatch_fails(self):
        with self.assertRaisesRegex(
            ValueError,
            "App ID does not match",
        ):
            validate_install_request(
                make_request(
                    appId="wrong-app"
                ),
                CATALOG,
            )

    def test_confirmation_mismatch_fails(self):
        with self.assertRaisesRegex(
            ValueError,
            "confirmation token",
        ):
            validate_install_request(
                make_request(
                    confirmation="WRONG"
                ),
                CATALOG,
            )

    def test_missing_storage_target_fails(self):
        with self.assertRaisesRegex(
            ValueError,
            "Storage target is required",
        ):
            validate_install_request(
                make_request(
                    storageTargetId=""
                ),
                CATALOG,
            )

    def test_short_rpc_password_fails(self):
        with self.assertRaisesRegex(
            ValueError,
            "at least 24 characters",
        ):
            validate_install_request(
                make_request(
                    rpcPassword="short"
                ),
                CATALOG,
            )

    def test_rpc_port_mismatch_fails(self):
        with self.assertRaisesRegex(
            ValueError,
            "RPC port does not match",
        ):
            validate_install_request(
                make_request(
                    rpcPort=9999
                ),
                CATALOG,
            )

    def test_p2p_port_mismatch_fails(self):
        with self.assertRaisesRegex(
            ValueError,
            "P2P port does not match",
        ):
            validate_install_request(
                make_request(
                    p2pPort=9999
                ),
                CATALOG,
            )

    def test_monero_none_auth_does_not_require_credentials(self):
        request = InstallRequest.from_dict({
            "providerId": "monero-mainnet",
            "appId": "seymour-monero-node",
            "nodeName": "Monero Node",
            "rpcUser": "",
            "rpcPassword": "",
            "rpcPort": 18081,
            "p2pPort": 18080,
            "storageTargetId": "storage-1",
            "confirmation":
                "INSTALL-seymour-monero-node",
        })

        validate_install_request(
            request,
            CATALOG,
        )

    def test_coming_soon_without_runtime_fails_closed(self):
        request = InstallRequest.from_dict({
            "providerId": "litecoin-mainnet",
            "appId": "seymour-litecoin-node",
            "nodeName": "Litecoin Node",
            "rpcUser": "",
            "rpcPassword": "",
            "rpcPort": 9332,
            "p2pPort": 9333,
            "storageTargetId": "storage-1",
            "confirmation":
                "INSTALL-seymour-litecoin-node",
        })

        with self.assertRaisesRegex(
            ValueError,
            "runtime contract is missing",
        ):
            validate_install_request(
                request,
                CATALOG,
            )


if __name__ == "__main__":
    unittest.main()
