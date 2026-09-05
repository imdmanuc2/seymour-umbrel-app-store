from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from shared.blockchain_install import StorageTargetType


ROOT = Path(__file__).resolve().parents[1]
WEB = (
    ROOT
    / "seymour-blockchain-manager"
    / "data"
    / "web"
)

if str(WEB) not in sys.path:
    sys.path.insert(0, str(WEB))

SPEC = importlib.util.spec_from_file_location(
    "manager_preflight_semantics",
    WEB / "installer.py",
)

installer = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = installer
assert SPEC.loader is not None
SPEC.loader.exec_module(installer)


class ManagerPreflightSemanticsTests(
    unittest.TestCase
):
    def _target(self, target_id, free_bytes):
        return installer.StorageTarget(
            target_id=target_id,
            target_type=(
                StorageTargetType.LOCAL
            ),
            host="test",
            path=f"/{target_id}",
            filesystem="ext4",
            source=f"/dev/{target_id}",
            total_bytes=free_bytes,
            used_bytes=0,
            free_bytes=free_bytes,
            writable=True,
            persistent=True,
            reachable=True,
        )

    def test_missing_explicit_target_does_not_fallback(self):
        fallback = self._target(
            "fallback",
            2_000_000_000_000,
        )

        inventory = {
            "targets": [
                fallback.to_dict(),
            ],
        }

        with (
            patch.object(
                installer,
                "storage_targets",
                return_value=inventory,
            ),
            patch.object(
                installer,
                "target_by_id",
                side_effect=lambda value: (
                    fallback
                    if value == "fallback"
                    else None
                ),
            ),
            patch.object(
                installer,
                "_network_available",
                return_value=True,
            ),
        ):
            result = installer.preflight(
                storage_target_id="missing",
                provider_id="bitcoin-mainnet",
                allow_storage_fallback=False,
            )

        self.assertFalse(result["compatible"])
        self.assertIsNone(
            result["checks"][
                "selectedStorageTargetId"
            ]
        )
        self.assertIn(
            "Selected storage target is unavailable.",
            result["errors"],
        )

    def test_wizard_without_target_can_fallback(self):
        fallback = self._target(
            "fallback",
            2_000_000_000_000,
        )

        inventory = {
            "targets": [
                fallback.to_dict(),
            ],
        }

        with (
            patch.object(
                installer,
                "storage_targets",
                return_value=inventory,
            ),
            patch.object(
                installer,
                "target_by_id",
                return_value=fallback,
            ),
            patch.object(
                installer,
                "_network_available",
                return_value=True,
            ),
            patch.object(
                installer,
                "_port_available",
                return_value=True,
            ),
            patch.object(
                installer,
                "evaluate_install_preflight",
            ) as evaluate,
        ):
            evaluate.return_value = type(
                "Result",
                (),
                {
                    "errors": [],
                    "to_dict": lambda self: {},
                },
            )()

            result = installer.preflight(
                storage_target_id=None,
                provider_id="bitcoin-mainnet",
            )

        self.assertEqual(
            result["checks"][
                "selectedStorageTargetId"
            ],
            "fallback",
        )

    def test_provider_runtime_uses_canonical_app_id(self):
        runtime = installer.provider_runtime(
            "bitcoin-mainnet"
        )

        self.assertEqual(
            runtime["appId"],
            "seymour-bitcoin-node",
        )

        self.assertNotIn(
            "appId",
            installer.INSTALL_ADAPTERS[
                "bitcoin-mainnet"
            ],
        )

        self.assertNotIn(
            "appId",
            installer.INSTALL_ADAPTERS[
                "bitcoin-cash-mainnet"
            ],
        )

        self.assertNotIn(
            "appId",
            installer.INSTALL_ADAPTERS[
                "monero-mainnet"
            ],
        )


if __name__ == "__main__":
    unittest.main()
