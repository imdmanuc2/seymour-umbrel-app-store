from __future__ import annotations

import stat
import tempfile
import unittest
from pathlib import Path

from shared.blockchain_install.runtime_binding_handoff import (
    RUNTIME_BINDING_FILENAME,
    app_runtime_binding_path,
    stage_runtime_binding,
)


class RuntimeBindingHandoffTests(
    unittest.TestCase
):
    def test_path_matches_umbrel_app_data_contract(
        self,
    ):
        value = app_runtime_binding_path(
            data_directory=Path(
                "/home/umbrel/umbrel"
            ),
            app_id="seymour-bch-node",
        )

        self.assertEqual(
            value,
            Path(
                "/home/umbrel/umbrel/"
                "app-data/seymour-bch-node/"
                "data/runtime-binding.env"
            ),
        )

    def test_stage_copies_exact_payload(
        self,
    ):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            source = root / "binding.env"
            source.write_bytes(
                b"SEYMOUR_BLOCKCHAIN_DATA_PATH=/mnt/node\n"
            )

            result = stage_runtime_binding(
                binding_path=source,
                data_directory=root / "umbrel",
                app_id="seymour-monero-node",
            )

            target = app_runtime_binding_path(
                data_directory=root / "umbrel",
                app_id="seymour-monero-node",
            )

            self.assertTrue(
                target.is_file()
            )

            self.assertEqual(
                target.read_bytes(),
                source.read_bytes(),
            )

            self.assertEqual(
                result["bindingFile"],
                str(target),
            )

            self.assertTrue(
                result["staged"]
            )

    def test_staged_file_mode_is_0600(
        self,
    ):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "binding.env"

            source.write_text(
                "VALUE=test\n"
            )

            stage_runtime_binding(
                binding_path=source,
                data_directory=root / "umbrel",
                app_id="seymour-bch-node",
            )

            target = app_runtime_binding_path(
                data_directory=root / "umbrel",
                app_id="seymour-bch-node",
            )

            self.assertEqual(
                stat.S_IMODE(
                    target.stat().st_mode
                ),
                0o600,
            )

    def test_stage_is_idempotent(
        self,
    ):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "binding.env"

            source.write_text(
                "VALUE=one\n"
            )

            kwargs = {
                "binding_path": source,
                "data_directory": root / "umbrel",
                "app_id": "seymour-bch-node",
            }

            stage_runtime_binding(**kwargs)
            stage_runtime_binding(**kwargs)

            target = app_runtime_binding_path(
                data_directory=root / "umbrel",
                app_id="seymour-bch-node",
            )

            self.assertEqual(
                target.read_text(),
                "VALUE=one\n",
            )

    def test_invalid_app_ids_fail_closed(
        self,
    ):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "binding.env"
            source.write_text(
                "VALUE=test\n"
            )

            for app_id in (
                "",
                ".",
                "..",
                "../escape",
                "bad/app",
                "bad\\app",
                "Bad App",
            ):
                with self.subTest(
                    app_id=app_id
                ):
                    with self.assertRaises(
                        ValueError
                    ):
                        stage_runtime_binding(
                            binding_path=source,
                            data_directory=(
                                root / "umbrel"
                            ),
                            app_id=app_id,
                        )

    def test_missing_source_fails_before_creation(
        self,
    ):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            target = (
                root
                / "umbrel"
                / "app-data"
                / "seymour-bch-node"
                / "data"
                / RUNTIME_BINDING_FILENAME
            )

            with self.assertRaises(
                ValueError
            ):
                stage_runtime_binding(
                    binding_path=(
                        root / "missing.env"
                    ),
                    data_directory=(
                        root / "umbrel"
                    ),
                    app_id=(
                        "seymour-bch-node"
                    ),
                )

            self.assertFalse(
                target.exists()
            )


if __name__ == "__main__":
    unittest.main()
