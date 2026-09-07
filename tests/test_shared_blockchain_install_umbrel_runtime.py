from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import (
    MagicMock,
    patch,
)

from shared.blockchain_install.umbrel_runtime import (
    build_umbrel_target_install_adapter,
    canonical_provider_controls,
    default_bch_local_data_path,
    neutral_binding_config_root,
    neutral_control_evidence_root,
)
from shared.blockchain_install.umbrel_target import (
    UmbrelTargetInstallAdapter,
)


class SharedUmbrelRuntimeFactoryTests(
    unittest.TestCase
):
    def test_canonical_provider_controls_use_root_scripts(
        self,
    ):
        repository = Path("/srv/seymour")

        controls = canonical_provider_controls(
            repository
        )

        self.assertEqual(
            set(controls),
            {
                "bitcoin-mainnet",
                "bitcoin-cash-mainnet",
                "monero-mainnet",
            },
        )

        expected = {
            "bitcoin-mainnet": (
                "seymour-install-btc",
                "BTC",
            ),
            "bitcoin-cash-mainnet": (
                "seymour-install-bch",
                "BCH",
            ),
            "monero-mainnet": (
                "seymour-install-monero",
                "XMR",
            ),
        }

        for provider_id, (
            filename,
            prefix,
        ) in expected.items():
            control = controls[
                provider_id
            ]

            self.assertEqual(
                control.install_script,
                repository
                / "scripts"
                / filename,
            )
            self.assertEqual(
                control.rpc_prefix,
                prefix,
            )
            self.assertNotIn(
                "seymour-blockchain-manager",
                str(
                    control.install_script
                ),
            )

    def test_neutral_paths_are_not_manager_owned(
        self,
    ):
        root = Path("/srv/umbrel")

        binding = neutral_binding_config_root(
            root
        )
        evidence = neutral_control_evidence_root(
            root
        )

        self.assertEqual(
            binding,
            root
            / "seymour-evidence"
            / "blockchain-install"
            / "runtime-bindings",
        )
        self.assertEqual(
            evidence,
            root
            / "seymour-evidence"
            / "blockchain-install"
            / "app-control",
        )

        self.assertNotIn(
            "seymour-blockchain-manager",
            str(binding),
        )
        self.assertNotIn(
            "seymour-blockchain-manager",
            str(evidence),
        )

    def test_default_bch_path_is_derived_from_data_root(
        self,
    ):
        root = Path("/srv/umbrel")

        self.assertEqual(
            default_bch_local_data_path(
                root
            ),
            root
            / "app-data"
            / "seymour-bch-node"
            / "data"
            / "node",
        )

    def test_relative_paths_fail_closed(
        self,
    ):
        with self.assertRaises(
            ValueError
        ):
            neutral_binding_config_root(
                Path("umbrel")
            )

        with self.assertRaises(
            ValueError
        ):
            neutral_control_evidence_root(
                Path("umbrel")
            )

        with self.assertRaises(
            ValueError
        ):
            default_bch_local_data_path(
                Path("umbrel")
            )

    @patch(
        "shared.blockchain_install."
        "umbrel_runtime."
        "UmbrelAppControlBridge"
    )
    def test_factory_constructs_real_adapter_without_execution(
        self,
        bridge_type,
    ):
        bridge = MagicMock()
        bridge_type.return_value = bridge

        adapter = (
            build_umbrel_target_install_adapter(
                repository=Path(
                    "/srv/seymour"
                ),
                umbrel_data_directory=Path(
                    "/srv/umbrel"
                ),
                remote_targets_path=Path(
                    "/etc/seymour/"
                    "storage-targets.json"
                ),
                runtime_host=(
                    "umbrel-target"
                ),
            )
        )

        self.assertIsInstance(
            adapter,
            UmbrelTargetInstallAdapter,
        )

        self.assertEqual(
            adapter.runtime_host,
            "umbrel-target",
        )
        self.assertEqual(
            adapter.umbrel_data_directory,
            Path("/srv/umbrel"),
        )
        self.assertEqual(
            adapter.binding_config_root,
            Path(
                "/srv/umbrel/"
                "seymour-evidence/"
                "blockchain-install/"
                "runtime-bindings"
            ),
        )
        self.assertEqual(
            adapter.bch_local_data_path,
            Path(
                "/srv/umbrel/"
                "app-data/"
                "seymour-bch-node/"
                "data/node"
            ),
        )

        bridge_type.assert_called_once()

        # Construction must not invoke Umbrel.
        bridge.execute.assert_not_called()

    @patch(
        "shared.blockchain_install."
        "umbrel_runtime."
        "UmbrelAppControlBridge"
    )
    def test_state_reader_normalizes_control_operation(
        self,
        bridge_type,
    ):
        operation = MagicMock()
        operation.to_dict.return_value = {
            "success": True,
            "result": {
                "state": "running",
            },
        }

        bridge = MagicMock()
        bridge.execute.return_value = (
            operation
        )
        bridge_type.return_value = bridge

        adapter = (
            build_umbrel_target_install_adapter(
                repository=Path(
                    "/srv/seymour"
                ),
                umbrel_data_directory=Path(
                    "/srv/umbrel"
                ),
                runtime_host=(
                    "umbrel-target"
                ),
            )
        )

        result = adapter.state_reader(
            "seymour-bitcoin-node"
        )

        bridge.execute.assert_called_once_with(
            "state",
            "seymour-bitcoin-node",
        )
        operation.to_dict.assert_called_once_with()

        self.assertEqual(
            result["success"],
            True,
        )
        self.assertEqual(
            result["result"]["state"],
            "running",
        )

    @patch(
        "shared.blockchain_install."
        "umbrel_runtime."
        "inspect_container_mounts"
    )
    @patch(
        "shared.blockchain_install."
        "umbrel_runtime."
        "discover_node_container"
    )
    @patch(
        "shared.blockchain_install."
        "umbrel_runtime."
        "UmbrelAppControlBridge"
    )
    def test_mount_reader_resolves_node_container(
        self,
        bridge_type,
        discover,
        inspect,
    ):
        bridge_type.return_value = (
            MagicMock()
        )
        discover.return_value = (
            "seymour-bitcoin-node-node-1"
        )
        inspect.return_value = [
            {
                "Destination": "/data",
            }
        ]

        adapter = (
            build_umbrel_target_install_adapter(
                repository=Path(
                    "/srv/seymour"
                ),
                umbrel_data_directory=Path(
                    "/srv/umbrel"
                ),
                runtime_host=(
                    "umbrel-target"
                ),
                docker_socket=Path(
                    "/run/docker.sock"
                ),
            )
        )

        result = adapter.mount_inspector(
            "seymour-bitcoin-node"
        )

        discover.assert_called_once_with(
            "seymour-bitcoin-node",
            socket_path=Path(
                "/run/docker.sock"
            ),
        )

        inspect.assert_called_once_with(
            "seymour-bitcoin-node-node-1",
            socket_path=Path(
                "/run/docker.sock"
            ),
        )

        self.assertEqual(
            result,
            [
                {
                    "Destination": "/data",
                }
            ],
        )

    def test_factory_rejects_relative_repository(
        self,
    ):
        with self.assertRaises(
            ValueError
        ):
            build_umbrel_target_install_adapter(
                repository=Path(
                    "seymour"
                ),
                umbrel_data_directory=Path(
                    "/srv/umbrel"
                ),
            )

    def test_factory_rejects_relative_data_root(
        self,
    ):
        with self.assertRaises(
            ValueError
        ):
            build_umbrel_target_install_adapter(
                repository=Path(
                    "/srv/seymour"
                ),
                umbrel_data_directory=Path(
                    "umbrel"
                ),
            )

    def test_custom_paths_remain_injectable(
        self,
    ):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)

            with patch(
                "shared.blockchain_install."
                "umbrel_runtime."
                "UmbrelAppControlBridge"
            ):
                adapter = (
                    build_umbrel_target_install_adapter(
                        repository=(
                            base / "repo"
                        ),
                        umbrel_data_directory=(
                            base / "umbrel"
                        ),
                        binding_config_root=(
                            base / "bindings"
                        ),
                        bch_local_data_path=(
                            base / "bch"
                        ),
                        runtime_host="host",
                    )
                )

            self.assertEqual(
                adapter.binding_config_root,
                base / "bindings",
            )
            self.assertEqual(
                adapter.bch_local_data_path,
                base / "bch",
            )


if __name__ == "__main__":
    unittest.main()
