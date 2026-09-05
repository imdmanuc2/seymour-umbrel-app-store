from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from shared.blockchain_install.umbrel_execution import (
    inspect_container_mounts,
    run_guarded_command,
    script_available,
)


class _Completed:
    returncode = 0
    stdout = '{"ok":true}\n'
    stderr = ""


class UmbrelExecutionPrimitiveTests(unittest.TestCase):
    def test_script_available_requires_executable_file(self):
        with tempfile.TemporaryDirectory() as value:
            path = Path(value) / "control"
            path.write_text("#!/bin/sh\nexit 0\n")

            self.assertFalse(script_available(path))

            path.chmod(0o755)

            self.assertTrue(script_available(path))

    def test_runner_uses_fixed_argv_without_shell(self):
        with tempfile.TemporaryDirectory() as value:
            script = Path(value) / "install"
            script.write_text("#!/bin/sh\nexit 0\n")
            script.chmod(0o755)

            with patch(
                "shared.blockchain_install."
                "umbrel_execution.subprocess.run",
                return_value=_Completed(),
            ) as runner:
                result = run_guarded_command(
                    (
                        str(script),
                        "--execute",
                        "--confirm",
                        "INSTALL-test",
                    ),
                    {
                        "BTC_RPC_PASSWORD":
                            "secret-not-in-argv",
                    },
                    900,
                )

            self.assertTrue(result.succeeded)

            args, kwargs = runner.call_args

            self.assertEqual(
                args[0],
                [
                    str(script),
                    "--execute",
                    "--confirm",
                    "INSTALL-test",
                ],
            )
            self.assertFalse(kwargs["shell"])
            self.assertEqual(
                kwargs["env"]["BTC_RPC_PASSWORD"],
                "secret-not-in-argv",
            )
            self.assertNotIn(
                "secret-not-in-argv",
                args[0],
            )

    def test_runner_fails_closed_for_missing_script(self):
        result = run_guarded_command(
            ("/definitely/missing/seymour-install",),
            {},
            10,
        )

        self.assertEqual(result.return_code, 127)
        self.assertFalse(result.succeeded)

    def test_mount_inspector_rejects_empty_name(self):
        with self.assertRaises(ValueError):
            inspect_container_mounts("")

    def test_module_has_no_management_product_import(self):
        source = Path(
            "shared/blockchain_install/"
            "umbrel_execution.py"
        ).read_text()

        self.assertNotIn(
            "seymour-blockchain-manager",
            source,
        )
        self.assertNotIn(
            "data.web",
            source,
        )


if __name__ == "__main__":
    unittest.main()
