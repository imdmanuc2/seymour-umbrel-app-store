from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]
BOOTSTRAP_FILE = PACKAGE / "scripts/bootstrap.py"

SPEC = importlib.util.spec_from_file_location(
    "sbp0772_bootstrap",
    BOOTSTRAP_FILE,
)

if SPEC is None or SPEC.loader is None:
    raise RuntimeError("unable to load bootstrap")

MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


RuntimeBootstrap = MODULE.RuntimeBootstrap
RuntimeBootstrapError = MODULE.RuntimeBootstrapError
file_sha256 = MODULE.file_sha256
safe_extract = MODULE.safe_extract


def make_archive(
    path: Path,
    members: list[tuple[str, bytes, int]],
) -> None:
    with tarfile.open(path, "w:gz") as handle:
        for name, data, mode in members:
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mode = mode

            handle.addfile(
                info,
                io.BytesIO(data),
            )


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_rejects_wrong_archive_hash_before_extract(self):
        archive = self.root / "runtime.tar.gz"

        make_archive(
            archive,
            [
                (
                    "seymour-runtime/file.txt",
                    b"data",
                    0o644,
                )
            ],
        )

        bootstrap = RuntimeBootstrap(
            umbrel_root=self.root,
        )

        with self.assertRaisesRegex(
            RuntimeBootstrapError,
            "reviewed SHA-256",
        ):
            bootstrap.install(
                archive=archive,
                archive_sha256="0" * 64,
                payload_manifest_sha256="1" * 64,
                runtime_version="1.0.0",
                source_revision="a" * 40,
            )

    def test_rejects_traversal(self):
        archive = self.root / "runtime.tar.gz"

        make_archive(
            archive,
            [
                (
                    "seymour-runtime/../escape",
                    b"bad",
                    0o644,
                )
            ],
        )

        with self.assertRaisesRegex(
            RuntimeBootstrapError,
            "unsafe path",
        ):
            safe_extract(
                archive,
                self.root / "extract",
            )

    def test_rejects_wrong_root(self):
        archive = self.root / "runtime.tar.gz"

        make_archive(
            archive,
            [
                (
                    "other/file",
                    b"bad",
                    0o644,
                )
            ],
        )

        with self.assertRaisesRegex(
            RuntimeBootstrapError,
            "invalid root",
        ):
            safe_extract(
                archive,
                self.root / "extract",
            )

    def test_rejects_symlink(self):
        archive = self.root / "runtime.tar.gz"

        with tarfile.open(archive, "w:gz") as handle:
            info = tarfile.TarInfo(
                "seymour-runtime/link"
            )
            info.type = tarfile.SYMTYPE
            info.linkname = "/etc/passwd"
            handle.addfile(info)

        with self.assertRaisesRegex(
            RuntimeBootstrapError,
            "links are prohibited",
        ):
            safe_extract(
                archive,
                self.root / "extract",
            )

    def test_safe_extract_restores_reviewed_modes(self):
        archive = self.root / "runtime.tar.gz"

        make_archive(
            archive,
            [
                (
                    "seymour-runtime/config.yml",
                    b"config",
                    0o664,
                ),
                (
                    "seymour-runtime/tool",
                    b"#!/bin/sh\n",
                    0o775,
                ),
            ],
        )

        extraction = self.root / "extract"
        extraction.mkdir()

        runtime = safe_extract(
            archive,
            extraction,
        )

        self.assertEqual(
            (
                runtime
                / "config.yml"
            ).stat().st_mode & 0o777,
            0o664,
        )

        self.assertEqual(
            (
                runtime
                / "tool"
            ).stat().st_mode & 0o777,
            0o775,
        )

    def test_rejects_special_permission_bits(self):
        archive = self.root / "runtime.tar.gz"

        make_archive(
            archive,
            [
                (
                    "seymour-runtime/tool",
                    b"data",
                    0o4755,
                )
            ],
        )

        extraction = self.root / "extract"
        extraction.mkdir()

        with self.assertRaisesRegex(
            RuntimeBootstrapError,
            "special permission bits",
        ):
            safe_extract(
                archive,
                extraction,
            )


    def test_safe_extract_returns_runtime_root(self):
        archive = self.root / "runtime.tar.gz"

        make_archive(
            archive,
            [
                (
                    "seymour-runtime/file.txt",
                    b"data",
                    0o644,
                )
            ],
        )

        extraction = self.root / "extract"
        extraction.mkdir()

        runtime = safe_extract(
            archive,
            extraction,
        )

        self.assertEqual(
            runtime,
            extraction / "seymour-runtime",
        )
        self.assertEqual(
            (runtime / "file.txt").read_bytes(),
            b"data",
        )

    def test_cli_failure_is_valid_json(self):
        import subprocess

        missing = self.root / "does-not-exist.tar.gz"

        result = subprocess.run(
            [
                sys.executable,
                str(BOOTSTRAP_FILE),
                "--archive",
                str(missing),
                "--archive-sha256",
                "0" * 64,
                "--payload-manifest-sha256",
                "1" * 64,
                "--runtime-version",
                "1.0.0",
                "--source-revision",
                "a" * 40,
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertNotEqual(
            result.returncode,
            0,
        )

        payload = json.loads(
            result.stdout.strip()
        )

        self.assertEqual(
            payload["success"],
            False,
        )

        self.assertIn(
            "runtime archive",
            payload["error"],
        )


    def test_public_cli_does_not_expose_target_root(self):
        import subprocess

        result = subprocess.run(
            [
                sys.executable,
                str(BOOTSTRAP_FILE),
                "--help",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0)

        help_text = result.stdout + result.stderr

        for forbidden in (
            "--target-root",
            "--umbrel-root",
            "--command",
            "--shell",
            "--argv",
            "--password",
            "--rpc-password",
        ):
            self.assertNotIn(
                forbidden,
                help_text,
            )


if __name__ == "__main__":
    unittest.main()
