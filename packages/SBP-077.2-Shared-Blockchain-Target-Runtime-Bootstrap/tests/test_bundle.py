from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tarfile
import unittest
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]
BUILD = PACKAGE / "build"

BUILDER = PACKAGE / "scripts" / "build.py"

BOOTSTRAP = (
    PACKAGE
    / "scripts"
    / "bootstrap.py"
)

INSTALLER = (
    PACKAGE.parent
    / "SBP-077.1-Shared-Blockchain-Target-Runtime-Installer"
    / "scripts"
    / "runtime_installer.py"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


class BootstrapBundleTests(unittest.TestCase):
    def tearDown(self):
        shutil.rmtree(
            BUILD,
            ignore_errors=True,
        )

    def build(self):
        completed = subprocess.run(
            [
                sys.executable,
                str(BUILDER),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(
            completed.returncode,
            0,
            completed.stderr,
        )

        return json.loads(
            completed.stdout.strip()
        )

    def test_bundle_is_exactly_two_files(self):
        result = self.build()

        archive = Path(
            result["archive"]
        )

        with tarfile.open(
            archive,
            "r:gz",
        ) as handle:
            members = handle.getmembers()

        self.assertEqual(
            [
                member.name
                for member in members
            ],
            [
                "seymour-bootstrap/bootstrap.py",
                "seymour-bootstrap/runtime_installer.py",
            ],
        )

        self.assertTrue(
            members[0].isfile()
        )

        self.assertTrue(
            members[1].isfile()
        )

        self.assertEqual(
            members[0].mode,
            0o755,
        )

        self.assertEqual(
            members[1].mode,
            0o644,
        )

    def test_bundle_metadata_matches_sources(self):
        self.build()

        metadata = json.loads(
            (
                BUILD
                / "seymour-bootstrap.artifact.json"
            ).read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(
            metadata["schemaVersion"],
            1,
        )

        self.assertEqual(
            metadata["artifactType"],
            "seymour-blockchain-target-bootstrap",
        )

        self.assertEqual(
            metadata["artifactVersion"],
            "1.0.0",
        )

        self.assertEqual(
            metadata["fileCount"],
            2,
        )

        self.assertEqual(
            metadata["files"],
            [
                {
                    "path": "bootstrap.py",
                    "sha256": sha256(
                        BOOTSTRAP
                    ),
                    "mode": "0755",
                },
                {
                    "path": "runtime_installer.py",
                    "sha256": sha256(
                        INSTALLER
                    ),
                    "mode": "0644",
                },
            ],
        )

        archive = (
            BUILD
            / "seymour-bootstrap.tar.gz"
        )

        self.assertEqual(
            metadata["archiveSha256"],
            sha256(archive),
        )

    def test_bundle_is_deterministic(self):
        first = self.build()

        first_archive = (
            BUILD
            / "seymour-bootstrap.tar.gz"
        ).read_bytes()

        first_metadata = (
            BUILD
            / "seymour-bootstrap.artifact.json"
        ).read_bytes()

        second = self.build()

        second_archive = (
            BUILD
            / "seymour-bootstrap.tar.gz"
        ).read_bytes()

        second_metadata = (
            BUILD
            / "seymour-bootstrap.artifact.json"
        ).read_bytes()

        self.assertEqual(
            first["archiveSha256"],
            second["archiveSha256"],
        )

        self.assertEqual(
            first_archive,
            second_archive,
        )

        self.assertEqual(
            first_metadata,
            second_metadata,
        )

    def test_bootstrap_defaults_to_bundled_installer(self):
        spec = importlib.util.spec_from_file_location(
            "sbp0772_bundle_lookup",
            BOOTSTRAP,
        )

        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)

        module = importlib.util.module_from_spec(
            spec
        )

        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        instance = module.RuntimeBootstrap(
            umbrel_root=Path("/tmp")
        )

        self.assertEqual(
            instance.installer_module_path,
            BOOTSTRAP.with_name(
                "runtime_installer.py"
            ),
        )


if __name__ == "__main__":
    unittest.main()
