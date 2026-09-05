from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from shared.blockchain_install.models import (
    StorageTarget,
    StorageTargetType,
)
from shared.blockchain_install.storage_inventory import (
    sort_storage_targets,
    storage_target_by_id,
    storage_target_inventory,
)


def target(
    target_id: str,
    target_type: StorageTargetType,
    path: str,
    free_bytes: int,
) -> StorageTarget:
    return StorageTarget(
        target_id=target_id,
        target_type=target_type,
        host="umbrel",
        path=path,
        filesystem="ext4",
        source="/dev/test",
        total_bytes=1000,
        used_bytes=100,
        free_bytes=free_bytes,
        writable=True,
        persistent=True,
        reachable=True,
    )


class StorageInventoryTests(unittest.TestCase):
    def test_sort_order_is_stable(self):
        values = [
            target(
                "remote",
                StorageTargetType.REMOTE,
                "/remote",
                900,
            ),
            target(
                "attached",
                StorageTargetType.ATTACHED,
                "/attached",
                800,
            ),
            target(
                "local",
                StorageTargetType.LOCAL,
                "/local",
                100,
            ),
        ]

        result = sort_storage_targets(values)

        self.assertEqual(
            [item.target_id for item in result],
            ["local", "attached", "remote"],
        )

    @patch(
        "shared.blockchain_install.storage_inventory."
        "registered_remote_targets"
    )
    @patch(
        "shared.blockchain_install.storage_inventory."
        "discover"
    )
    def test_inventory_combines_discovered_and_registered(
        self,
        discover_mock,
        remote_mock,
    ):
        local = target(
            "local",
            StorageTargetType.LOCAL,
            "/local",
            100,
        )
        remote = target(
            "remote",
            StorageTargetType.REMOTE,
            "/remote",
            900,
        )

        discover_mock.return_value = [local]
        remote_mock.return_value = [remote]

        result = storage_target_inventory(
            local_path=Path("/local"),
            remote_targets_path=Path("/targets.json"),
        )

        self.assertEqual(
            [item.target_id for item in result],
            ["local", "remote"],
        )

    @patch(
        "shared.blockchain_install.storage_inventory."
        "storage_target_inventory"
    )
    def test_exact_target_resolution(
        self,
        inventory_mock,
    ):
        local = target(
            "local",
            StorageTargetType.LOCAL,
            "/local",
            100,
        )

        inventory_mock.return_value = [local]

        self.assertIs(
            storage_target_by_id(
                "local",
                local_path=Path("/local"),
            ),
            local,
        )

        self.assertIsNone(
            storage_target_by_id(
                "missing",
                local_path=Path("/local"),
            )
        )

    def test_empty_target_id_fails_closed(self):
        self.assertIsNone(
            storage_target_by_id(
                "",
                local_path=Path("/local"),
            )
        )

    def test_invalid_remote_json_is_ignored(self):
        from shared.blockchain_install.storage_inventory import (
            registered_remote_targets,
        )

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "targets.json"
            path.write_text("{broken")

            self.assertEqual(
                registered_remote_targets(path),
                [],
            )


if __name__ == "__main__":
    unittest.main()
