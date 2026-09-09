from __future__ import annotations

import importlib.machinery
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "seymour-storage-materialize"


def load_cli():
    loader = importlib.machinery.SourceFileLoader(
        "seymour_storage_materialize_cli",
        str(SCRIPT),
    )
    spec = importlib.util.spec_from_loader(
        loader.name,
        loader,
    )
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class MaterializationRegistryHandoffTests(unittest.TestCase):
    def setUp(self):
        self.cli = load_cli()

    def _run(
        self,
        *,
        root: Path,
        healthy: bool,
        mount_success: bool = True,
        role: str = "runtime-host",
    ):
        evidence = root / "evidence.json"
        umbrel = root / "umbrel"
        mount = root / "mount"
        mount.mkdir(parents=True)
        umbrel.mkdir(parents=True)

        argv = [
            str(SCRIPT),
            "--provider-id",
            "bitcoin-mainnet",
            "--storage-host",
            "storage.example",
            "--storage-path",
            "/srv/seymour",
            "--runtime-host",
            "runtime.example",
            "--runtime-mount-path",
            str(mount),
            "--role",
            role,
            "--execute",
            "--confirm",
            (
                "MATERIALIZE-bitcoin-mainnet-"
                "ON-storage.example"
            ),
            "--evidence-path",
            str(evidence),
        ]

        verification = {
            "path": str(mount),
            "exists": True,
            "mounted": healthy,
            "writable": healthy,
            "freeBytes": 10**12,
            "healthy": healthy,
        }

        with (
            patch.object(sys, "argv", argv),
            patch.object(
                self.cli,
                "UMBREL_DATA_DIRECTORY",
                umbrel,
            ),
            patch.object(
                self.cli,
                "command_available",
                return_value=True,
            ),
            patch.object(
                self.cli,
                "ensure_line",
                return_value=True,
            ),
            patch.object(
                self.cli,
                "run",
                return_value={
                    "command": ["mount", str(mount)],
                    "returnCode": (
                        0 if mount_success else 1
                    ),
                    "stdout": "",
                    "stderr": "",
                    "success": mount_success,
                },
            ),
            patch.object(
                self.cli,
                "verify_mount",
                return_value=verification,
            ),
        ):
            with self.assertRaises(SystemExit) as exc:
                self.cli.main()

        payload = (
            json.loads(evidence.read_text())
            if evidence.exists()
            else None
        )

        registry = (
            umbrel
            / "seymour-evidence"
            / "blockchain-install"
            / "storage-targets.json"
        )

        return exc.exception.code, payload, registry

    def test_verified_runtime_mount_registers_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, payload, registry = self._run(
                root=Path(tmp),
                healthy=True,
            )

            self.assertEqual(code, 0)
            self.assertTrue(payload["success"])
            self.assertTrue(registry.is_file())

            stored = json.loads(registry.read_text())

            self.assertEqual(
                len(stored["targets"]),
                1,
            )
            self.assertEqual(
                payload["storageTarget"]["targetId"],
                stored["targets"][0]["targetId"],
            )
            self.assertEqual(
                stored["targets"][0]["remoteHost"],
                "storage.example",
            )
            self.assertEqual(
                stored["targets"][0]["source"],
                "storage.example:/srv/seymour",
            )

            self.assertNotEqual(
                stored["targets"][0]["targetId"],
                "",
            )

    def test_registration_failure_preserves_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "evidence.json"
            umbrel = root / "umbrel"
            mount = root / "mount"

            mount.mkdir()
            umbrel.mkdir()

            argv = [
                str(SCRIPT),
                "--provider-id",
                "bitcoin-mainnet",
                "--storage-host",
                "storage.example",
                "--storage-path",
                "/srv/seymour",
                "--runtime-host",
                "runtime.example",
                "--runtime-mount-path",
                str(mount),
                "--role",
                "runtime-host",
                "--execute",
                "--confirm",
                (
                    "MATERIALIZE-bitcoin-mainnet-"
                    "ON-storage.example"
                ),
                "--evidence-path",
                str(evidence),
            ]

            verification = {
                "path": str(mount),
                "exists": True,
                "mounted": True,
                "writable": True,
                "freeBytes": 10**12,
                "healthy": True,
            }

            with (
                patch.object(sys, "argv", argv),
                patch.object(
                    self.cli,
                    "UMBREL_DATA_DIRECTORY",
                    umbrel,
                ),
                patch.object(
                    self.cli,
                    "command_available",
                    return_value=True,
                ),
                patch.object(
                    self.cli,
                    "ensure_line",
                    return_value=True,
                ),
                patch.object(
                    self.cli,
                    "run",
                    return_value={
                        "command": [
                            "mount",
                            str(mount),
                        ],
                        "returnCode": 0,
                        "stdout": "",
                        "stderr": "",
                        "success": True,
                    },
                ),
                patch.object(
                    self.cli,
                    "verify_mount",
                    return_value=verification,
                ),
                patch.object(
                    self.cli,
                    "register_remote_target",
                    side_effect=OSError(
                        "simulated registry write failure"
                    ),
                ),
            ):
                with self.assertRaises(SystemExit) as exc:
                    self.cli.main()

            self.assertEqual(
                exc.exception.code,
                1,
            )
            self.assertTrue(
                evidence.is_file()
            )

            payload = json.loads(
                evidence.read_text()
            )

            self.assertFalse(
                payload["success"]
            )
            self.assertTrue(
                payload["executed"]
            )
            self.assertTrue(
                payload["verification"]["healthy"]
            )
            self.assertEqual(
                payload["error"],
                "storage-target-registration-failed",
            )
            self.assertIn(
                "simulated registry write failure",
                payload["registrationError"],
            )
            self.assertNotIn(
                "storageTarget",
                payload,
            )

    def test_unhealthy_mount_does_not_register_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, payload, registry = self._run(
                root=Path(tmp),
                healthy=False,
            )

            self.assertEqual(code, 1)
            self.assertFalse(payload["success"])
            self.assertFalse(registry.exists())

    def test_failed_mount_does_not_register_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, payload, registry = self._run(
                root=Path(tmp),
                healthy=False,
                mount_success=False,
            )

            self.assertEqual(code, 1)
            self.assertFalse(payload["success"])
            self.assertFalse(registry.exists())

    def test_plan_mode_cannot_register_target(self):
        cli = load_cli()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            umbrel = root / "umbrel"
            umbrel.mkdir()

            argv = [
                str(SCRIPT),
                "--provider-id",
                "bitcoin-mainnet",
                "--storage-host",
                "storage.example",
                "--storage-path",
                "/srv/seymour",
                "--runtime-host",
                "runtime.example",
                "--runtime-mount-path",
                str(root / "mount"),
                "--role",
                "runtime-host",
            ]

            with (
                patch.object(sys, "argv", argv),
                patch.object(
                    cli,
                    "UMBREL_DATA_DIRECTORY",
                    umbrel,
                ),
            ):
                with self.assertRaises(SystemExit) as exc:
                    cli.main()

            self.assertEqual(exc.exception.code, 0)

            registry = (
                umbrel
                / "seymour-evidence"
                / "blockchain-install"
                / "storage-targets.json"
            )

            self.assertFalse(registry.exists())


if __name__ == "__main__":
    unittest.main()
