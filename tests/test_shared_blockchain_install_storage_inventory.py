from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from shared.blockchain_install.models import (
    StorageTarget,
    StorageTargetType,
)
from shared.blockchain_install.storage_inventory import (
    register_remote_target,
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


    def test_register_remote_target_is_atomic_and_idempotent(
        self,
    ):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "storage-targets.json"

            first = register_remote_target(
                path,
                mount_path=Path("/mnt/seymour-storage"),
                remote_host="storage.example",
                source=(
                    "storage.example:"
                    "/srv/seymour"
                ),
                filesystem="nfs4",
            )

            second = register_remote_target(
                path,
                mount_path=Path("/mnt/seymour-storage"),
                remote_host="storage.example",
                source=(
                    "storage.example:"
                    "/srv/seymour"
                ),
                filesystem="nfs4",
            )

            self.assertEqual(first, second)
            self.assertEqual(
                len(second["targets"]),
                1,
            )
            temporary_files = list(
                root.glob(
                    f".{path.name}.*.tmp"
                )
            )
            self.assertEqual(
                temporary_files,
                [],
            )

            persisted = json.loads(
                path.read_text()
            )
            self.assertEqual(
                persisted,
                second,
            )

    def test_register_remote_target_fsyncs_file_and_directory(
        self,
    ):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "storage-targets.json"

            with patch(
                "shared.blockchain_install."
                "storage_inventory.os.fsync",
                wraps=os.fsync,
            ) as fsync:
                register_remote_target(
                    path,
                    mount_path=Path("/mnt/seymour-storage"),
                    remote_host="storage.example",
                    source="storage.example:/srv/seymour",
                    filesystem="nfs4",
                )

            self.assertGreaterEqual(
                fsync.call_count,
                2,
            )
            self.assertTrue(path.is_file())

    def test_register_remote_target_cleans_temp_on_replace_failure(
        self,
    ):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "storage-targets.json"

            with patch(
                "shared.blockchain_install."
                "storage_inventory.os.replace",
                side_effect=OSError(
                    "simulated replace failure"
                ),
            ):
                with self.assertRaisesRegex(
                    OSError,
                    "simulated replace failure",
                ):
                    register_remote_target(
                        path,
                        mount_path=Path("/mnt/seymour-storage"),
                        remote_host="storage.example",
                        source="storage.example:/srv/seymour",
                        filesystem="nfs4",
                    )

            self.assertFalse(path.exists())
            self.assertEqual(
                list(
                    root.glob(
                        f".{path.name}.*.tmp"
                    )
                ),
                [],
            )

    def test_register_remote_target_preserves_other_targets(
        self,
    ):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "storage-targets.json"

            register_remote_target(
                path,
                mount_path=Path("/mnt/one"),
                remote_host="one.example",
                source="one.example:/srv/one",
            )

            result = register_remote_target(
                path,
                mount_path=Path("/mnt/two"),
                remote_host="two.example",
                source="two.example:/srv/two",
            )

            self.assertEqual(
                len(result["targets"]),
                2,
            )

    def test_register_remote_target_updates_same_identity(
        self,
    ):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "storage-targets.json"

            register_remote_target(
                path,
                mount_path=Path("/mnt/remote"),
                remote_host="store.example",
                source="store.example:/srv/data",
                filesystem="nfs",
            )

            result = register_remote_target(
                path,
                mount_path=Path("/mnt/remote"),
                remote_host="store.example",
                source="store.example:/srv/data",
                filesystem="nfs4",
            )

            self.assertEqual(
                len(result["targets"]),
                1,
            )
            self.assertEqual(
                result["targets"][0]["filesystem"],
                "nfs4",
            )

    def test_register_remote_target_rejects_relative_registry(
        self,
    ):
        with self.assertRaises(ValueError):
            register_remote_target(
                Path("relative/storage-targets.json"),
                mount_path=Path("/mnt/remote"),
                remote_host="store.example",
                source="store.example:/srv/data",
            )

    def test_register_remote_target_rejects_relative_mount(
        self,
    ):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                register_remote_target(
                    Path(tmp) / "storage-targets.json",
                    mount_path=Path("relative/mount"),
                    remote_host="store.example",
                    source="store.example:/srv/data",
                )

    def test_register_remote_target_fails_closed_on_invalid_existing_registry(
        self,
    ):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "storage-targets.json"
            path.write_text("{broken")

            with self.assertRaises(ValueError):
                register_remote_target(
                    path,
                    mount_path=Path("/mnt/remote"),
                    remote_host="store.example",
                    source="store.example:/srv/data",
                )

            self.assertEqual(
                path.read_text(),
                "{broken",
            )


    def test_register_remote_target_replaces_changed_source_for_same_target(
        self,
    ):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "storage-targets.json"

            first = register_remote_target(
                path,
                mount_path=Path("/mnt/remote"),
                remote_host="old.example",
                source="old.example:/srv/data",
                runtime_host="umbrel-runtime",
            )

            second = register_remote_target(
                path,
                mount_path=Path("/mnt/remote"),
                remote_host="new.example",
                source="new.example:/srv/data",
                runtime_host="umbrel-runtime",
            )

            self.assertEqual(
                len(second["targets"]),
                1,
            )
            self.assertEqual(
                first["targets"][0]["targetId"],
                second["targets"][0]["targetId"],
            )
            self.assertEqual(
                second["targets"][0]["remoteHost"],
                "new.example",
            )
            self.assertEqual(
                second["targets"][0]["source"],
                "new.example:/srv/data",
            )

    def test_registered_nfs4_accepts_live_nfs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / "storage-targets.json"
            mount = root / "remote"
            local = root / "local"
            mount.mkdir()
            local.mkdir()

            with patch(
                "shared.blockchain_install."
                "storage_inventory.socket.gethostname",
                return_value="target-host",
            ):
                result = register_remote_target(
                    registry,
                    mount_path=mount,
                    remote_host="store.example",
                    source="store.example:/srv/data",
                    filesystem="nfs4",
                )

            target_id = result["targets"][0]["targetId"]

            with (
                patch(
                    "shared.blockchain_install."
                    "storage.socket.gethostname",
                    return_value="target-host",
                ),
                patch(
                    "shared.blockchain_install."
                    "storage.read_mounts",
                    return_value=[
                        {
                            "source": "store.example:/srv/data",
                            "mountPoint": str(mount.resolve()),
                            "filesystem": "nfs",
                            "options": "rw",
                        }
                    ],
                ),
            ):
                resolved = storage_target_by_id(
                    target_id,
                    local_path=local,
                    remote_targets_path=registry,
                )

            self.assertEqual(
                resolved.target_id,
                target_id,
            )
            self.assertEqual(
                resolved.filesystem,
                "nfs",
            )

    def test_registered_nfs_accepts_live_nfs4(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / "storage-targets.json"
            mount = root / "remote"
            local = root / "local"
            mount.mkdir()
            local.mkdir()

            with patch(
                "shared.blockchain_install."
                "storage_inventory.socket.gethostname",
                return_value="target-host",
            ):
                result = register_remote_target(
                    registry,
                    mount_path=mount,
                    remote_host="store.example",
                    source="store.example:/srv/data",
                    filesystem="nfs",
                )

            target_id = result["targets"][0]["targetId"]

            with (
                patch(
                    "shared.blockchain_install."
                    "storage.socket.gethostname",
                    return_value="target-host",
                ),
                patch(
                    "shared.blockchain_install."
                    "storage.read_mounts",
                    return_value=[
                        {
                            "source": "store.example:/srv/data",
                            "mountPoint": str(mount.resolve()),
                            "filesystem": "nfs4",
                            "options": "rw",
                        }
                    ],
                ),
            ):
                resolved = storage_target_by_id(
                    target_id,
                    local_path=local,
                    remote_targets_path=registry,
                )

            self.assertEqual(
                resolved.target_id,
                target_id,
            )
            self.assertEqual(
                resolved.filesystem,
                "nfs4",
            )

    def test_registered_nfs_rejects_non_nfs_filesystem(self):
        with tempfile.TemporaryDirectory() as tmp:
            mount = Path(tmp) / "remote"
            mount.mkdir()

            from shared.blockchain_install.storage import (
                registered_remote_target,
            )

            with patch(
                "shared.blockchain_install.storage.read_mounts",
                return_value=[
                    {
                        "source": "store.example:/srv/data",
                        "mountPoint": str(mount.resolve()),
                        "filesystem": "ext4",
                        "options": "rw",
                    }
                ],
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    "filesystem mismatch",
                ):
                    registered_remote_target(
                        mount_path=mount,
                        remote_host="store.example",
                        source="store.example:/srv/data",
                        filesystem="nfs4",
                        check_writable=False,
                    )

    def test_registered_target_id_matches_inventory_identity(
        self,
    ):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "storage-targets.json"
            mount = root / "remote"
            mount.mkdir()

            local = root / "local"
            local.mkdir()

            with patch(
                "shared.blockchain_install."
                "storage_inventory.socket.gethostname",
                return_value="actual-target-host",
            ):
                result = register_remote_target(
                    path,
                    mount_path=mount,
                    remote_host="store.example",
                    source="store.example:/srv/data",
                    filesystem="nfs4",
                )

            target_id = result["targets"][0]["targetId"]

            with (
                patch(
                    "shared.blockchain_install."
                    "storage.socket.gethostname",
                    return_value="actual-target-host",
                ),
                patch(
                    "shared.blockchain_install."
                    "storage.read_mounts",
                    return_value=[
                        {
                            "source": "store.example:/srv/data",
                            "mountPoint": str(mount.resolve()),
                            "filesystem": "nfs4",
                            "options": "rw",
                        }
                    ],
                ),
            ):
                resolved = storage_target_by_id(
                    target_id,
                    local_path=local,
                    remote_targets_path=path,
                )

            self.assertEqual(
                resolved.target_id,
                target_id,
            )
            self.assertEqual(
                resolved.path,
                str(mount.resolve()),
            )
            self.assertEqual(
                resolved.remote_host,
                "store.example",
            )



if __name__ == "__main__":
    unittest.main()
