from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from shared.umbrel_control.bridge import (
    UmbrelAppControlBridge,
)


class UmbrelControlRuntimeBindingDirectoryTests(
    unittest.TestCase
):
    def _bridge(
        self,
        *,
        data_directory: Path,
        runtime_binding_directory: Path | None = None,
    ) -> UmbrelAppControlBridge:
        return UmbrelAppControlBridge(
            helper_path=Path("/unused/helper.ts"),
            data_directory=data_directory,
            evidence_directory=(
                data_directory / "test-evidence"
            ),
            runtime_binding_directory=(
                runtime_binding_directory
            ),
        )

    def test_default_preserves_manager_compatibility(
        self,
    ) -> None:
        root = Path("/umbrel")

        bridge = self._bridge(
            data_directory=root,
        )

        self.assertEqual(
            bridge.runtime_binding_directory,
            (
                root
                / "app-data"
                / "seymour-blockchain-manager"
                / "data"
                / "evidence"
                / "runtime-bindings"
            ),
        )

    def test_injected_directory_is_used(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            binding_root = root / "shared-bindings"
            binding_root.mkdir()

            app_id = "seymour-bitcoin-node"
            binding_path = (
                binding_root / f"{app_id}.env"
            )
            binding_path.write_text(
                "placeholder=true\n"
            )

            bridge = self._bridge(
                data_directory=root,
                runtime_binding_directory=binding_root,
            )

            native_results = [
                True,
            ]

            with (
                patch.object(
                    bridge,
                    "_invoke",
                    side_effect=native_results,
                ),
                patch(
                    "shared.umbrel_control.bridge."
                    "reconcile_installed_runtime_binding",
                    return_value={
                        "changed": False,
                    },
                ) as reconcile,
            ):
                operation = bridge.execute(
                    "install",
                    app_id,
                    execute=True,
                    confirmation=(
                        f"INSTALL-{app_id}"
                    ),
                )

            self.assertTrue(operation.success)

            reconcile.assert_called_once_with(
                data_directory=root,
                binding_path=binding_path,
            )


if __name__ == "__main__":
    unittest.main()
