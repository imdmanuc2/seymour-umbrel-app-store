#!/usr/bin/env python3
from __future__ import annotations

import json
import tarfile
import unittest
import subprocess
import sys
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]


def run(script: str) -> None:
    result = subprocess.run(
        [sys.executable, str(PACKAGE / "scripts" / script)],
        text=True,
        capture_output=True,
        check=False,
    )

    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        raise SystemExit(result.returncode)


run("build.py")
run("verify.py")

print("packageBuildTest=PASS")


class DeterministicBundleTests(unittest.TestCase):
    def test_bundle_outputs_exist(self):
        build = PACKAGE / "build"

        self.assertTrue(
            (build / "seymour-runtime.tar.gz").is_file()
        )
        self.assertTrue(
            (
                build
                / "seymour-runtime.artifact.json"
            ).is_file()
        )

    def test_metadata_contract(self):
        build = PACKAGE / "build"

        metadata = json.loads(
            (
                build
                / "seymour-runtime.artifact.json"
            ).read_text(encoding="utf-8")
        )

        self.assertEqual(metadata["schemaVersion"], 1)
        self.assertEqual(
            metadata["artifactType"],
            "seymour-blockchain-target-runtime",
        )
        self.assertEqual(
            metadata["runtimeVersion"],
            "1.0.0",
        )
        self.assertEqual(
            len(metadata["sourceRevision"]),
            40,
        )
        self.assertEqual(
            len(metadata["archiveSha256"]),
            64,
        )
        self.assertEqual(
            len(metadata["payloadManifestSha256"]),
            64,
        )
        self.assertEqual(
            metadata["payloadFileCount"],
            51,
        )

    def test_archive_has_single_runtime_root(self):
        archive = (
            PACKAGE
            / "build"
            / "seymour-runtime.tar.gz"
        )

        with tarfile.open(archive, "r:gz") as handle:
            names = handle.getnames()

        self.assertTrue(names)

        for name in names:
            self.assertTrue(
                name == "seymour-runtime"
                or name.startswith("seymour-runtime/"),
                name,
            )

            self.assertNotIn(
                "..",
                Path(name).parts,
            )

    def test_archive_excludes_product_junk(self):
        archive = (
            PACKAGE
            / "build"
            / "seymour-runtime.tar.gz"
        )

        with tarfile.open(archive, "r:gz") as handle:
            names = handle.getnames()

        forbidden = (
            "seymour-blockchain-manager",
            "nexus-command-center",
            "__pycache__",
            ".git",
        )

        for name in names:
            for item in forbidden:
                self.assertNotIn(item, name)
