from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]

RUNTIME_PACKAGE = (
    ROOT
    / "packages"
    / "SBP-077-Shared-Blockchain-Target-Runtime"
)

BOOTSTRAP_PACKAGE = (
    ROOT
    / "packages"
    / "SBP-077.2-Shared-Blockchain-Target-Runtime-Bootstrap"
)

BOOTSTRAP_FILE = (
    BOOTSTRAP_PACKAGE
    / "scripts"
    / "bootstrap.py"
)


def load_bootstrap():
    spec = importlib.util.spec_from_file_location(
        "sbp0772_real_bundle_integration",
        BOOTSTRAP_FILE,
    )

    if spec is None or spec.loader is None:
        raise RuntimeError(
            "unable to load SBP-077.2 bootstrap"
        )

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    return module


class RealBundleIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        result = subprocess.run(
            [
                sys.executable,
                str(
                    RUNTIME_PACKAGE
                    / "scripts"
                    / "build.py"
                ),
            ],
            capture_output=True,
            text=True,
            check=False,
            env={
                **__import__("os").environ,
                "PYTHONDONTWRITEBYTECODE": "1",
            },
        )

        if result.returncode != 0:
            raise RuntimeError(
                "SBP-077 build failed:\n"
                + result.stdout
                + "\n"
                + result.stderr
            )

        verify = subprocess.run(
            [
                sys.executable,
                str(
                    RUNTIME_PACKAGE
                    / "scripts"
                    / "verify.py"
                ),
            ],
            capture_output=True,
            text=True,
            check=False,
            env={
                **__import__("os").environ,
                "PYTHONDONTWRITEBYTECODE": "1",
            },
        )

        if verify.returncode != 0:
            raise RuntimeError(
                "SBP-077 verification failed:\n"
                + verify.stdout
                + "\n"
                + verify.stderr
            )

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.umbrel_root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_actual_bundle_installs_through_bootstrap(self):
        module = load_bootstrap()

        build = (
            RUNTIME_PACKAGE
            / "build"
        )

        archive = (
            build
            / "seymour-runtime.tar.gz"
        )

        metadata = json.loads(
            (
                build
                / "seymour-runtime.artifact.json"
            ).read_text(
                encoding="utf-8"
            )
        )

        archive_sha = hashlib.sha256(
            archive.read_bytes()
        ).hexdigest()

        self.assertEqual(
            archive_sha,
            metadata["archiveSha256"],
        )

        bootstrap = module.RuntimeBootstrap(
            umbrel_root=self.umbrel_root,
        )

        result = bootstrap.install(
            archive=archive,
            archive_sha256=metadata[
                "archiveSha256"
            ],
            payload_manifest_sha256=metadata[
                "payloadManifestSha256"
            ],
            runtime_version=metadata[
                "runtimeVersion"
            ],
            source_revision=metadata[
                "sourceRevision"
            ],
        )

        self.assertTrue(
            result["success"]
        )

        self.assertEqual(
            result["archiveSha256"],
            metadata["archiveSha256"],
        )

        self.assertEqual(
            result["payloadManifestSha256"],
            metadata["payloadManifestSha256"],
        )

        installed = (
            self.umbrel_root
            / "seymour-runtime"
        )

        self.assertTrue(
            installed.is_dir()
        )

        self.assertTrue(
            (
                installed
                / "scripts"
                / "seymour-blockchain-install"
            ).is_file()
        )

        installer_module = (
            module.load_installer_module(
                module.RuntimeBootstrap(
                    umbrel_root=self.umbrel_root
                ).installer_module_path
            )
        )

        installer_module.verify_runtime(
            installed
        )

        installed_manifest, rows = (
            installer_module.payload_manifest(
                installed
            )
        )

        self.assertEqual(
            installed_manifest,
            metadata["payloadManifestSha256"],
        )

        self.assertEqual(
            len(rows),
            metadata["payloadFileCount"],
        )

        evidence_root = (
            self.umbrel_root
            / "seymour-evidence"
            / "blockchain-target-runtime"
        )

        current = (
            evidence_root
            / "current.json"
        )

        self.assertTrue(
            current.is_file()
        )

        current_payload = json.loads(
            current.read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(
            current_payload[
                "payloadManifestSha256"
            ],
            metadata[
                "payloadManifestSha256"
            ],
        )

        extraction_leftovers = list(
            self.umbrel_root.glob(
                ".seymour-runtime.extract.*"
            )
        )

        self.assertEqual(
            extraction_leftovers,
            [],
        )

    def test_wrong_payload_manifest_never_promotes(self):
        module = load_bootstrap()

        build = (
            RUNTIME_PACKAGE
            / "build"
        )

        archive = (
            build
            / "seymour-runtime.tar.gz"
        )

        metadata = json.loads(
            (
                build
                / "seymour-runtime.artifact.json"
            ).read_text(
                encoding="utf-8"
            )
        )

        bootstrap = module.RuntimeBootstrap(
            umbrel_root=self.umbrel_root,
        )

        with self.assertRaisesRegex(
            module.RuntimeBootstrapError,
            "reviewed payload manifest",
        ):
            bootstrap.install(
                archive=archive,
                archive_sha256=metadata[
                    "archiveSha256"
                ],
                payload_manifest_sha256=(
                    "0" * 64
                ),
                runtime_version=metadata[
                    "runtimeVersion"
                ],
                source_revision=metadata[
                    "sourceRevision"
                ],
            )

        self.assertFalse(
            (
                self.umbrel_root
                / "seymour-runtime"
            ).exists()
        )

        self.assertEqual(
            list(
                self.umbrel_root.glob(
                    ".seymour-runtime.extract.*"
                )
            ),
            [],
        )


if __name__ == "__main__":
    unittest.main()
