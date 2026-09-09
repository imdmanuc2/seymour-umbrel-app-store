#!/usr/bin/env python3
from __future__ import annotations

import fcntl
import importlib.util
import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]
MODULE_PATH = PACKAGE / "scripts/runtime_installer.py"

SPEC = importlib.util.spec_from_file_location(
    "runtime_installer",
    MODULE_PATH,
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def make_runtime(root: Path, marker: str) -> Path:
    artifact = root / f"artifact-{marker}"

    for relative in MODULE.REQUIRED_FILES:
        path = artifact / relative
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if relative.endswith("providers.v1.json"):
            path.write_text(
                json.dumps({"providers": []}),
                encoding="utf-8",
            )
        else:
            path.write_text(
                f"{relative}:{marker}\n",
                encoding="utf-8",
            )

    for relative in MODULE.EXECUTABLE_FILES:
        path = artifact / relative
        path.chmod(
            stat.S_IMODE(path.stat().st_mode) | 0o100
        )

    return artifact


class RuntimeInstallerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.umbrel = self.root / "umbrel"
        self.artifacts = self.root / "artifacts"
        self.artifacts.mkdir()

    def tearDown(self):
        self.temporary.cleanup()

    def installer(self, verifier=MODULE.verify_runtime):
        return MODULE.RuntimeInstaller(
            umbrel_root=self.umbrel,
            verifier=verifier,
        )

    def marker(self, runtime: Path) -> str:
        return (
            runtime
            / "shared/bch_install/workflow.py"
        ).read_text(encoding="utf-8").strip()

    def manifest(self, artifact: Path) -> str:
        return MODULE.payload_manifest(artifact)[0]

    def test_fresh_install(self):
        artifact = make_runtime(
            self.artifacts,
            "v1",
        )

        result = self.installer().install(
            artifact=artifact,
            runtime_version="1.0.0",
            source_revision="revision-v1",
            expected_manifest_sha256=self.manifest(artifact),
        )

        self.assertEqual(
            result["status"],
            "installed",
        )
        self.assertTrue(
            (self.umbrel / "seymour-runtime").is_dir()
        )
        self.assertFalse(
            (
                self.umbrel
                / "seymour-runtime.previous"
            ).exists()
        )

    def test_update_preserves_one_previous_runtime(self):
        first = make_runtime(
            self.artifacts,
            "v1",
        )
        second = make_runtime(
            self.artifacts,
            "v2",
        )

        installer = self.installer()

        installer.install(
            artifact=first,
            runtime_version="1",
            source_revision="r1",
            expected_manifest_sha256=self.manifest(first),
        )
        installer.install(
            artifact=second,
            runtime_version="2",
            source_revision="r2",
            expected_manifest_sha256=self.manifest(second),
        )

        self.assertIn(
            "v2",
            self.marker(
                self.umbrel / "seymour-runtime"
            ),
        )
        self.assertIn(
            "v1",
            self.marker(
                self.umbrel
                / "seymour-runtime.previous"
            ),
        )

    def test_explicit_rollback_swaps_current_and_previous(self):
        first = make_runtime(
            self.artifacts,
            "v1",
        )
        second = make_runtime(
            self.artifacts,
            "v2",
        )

        installer = self.installer()

        installer.install(
            artifact=first,
            runtime_version="1",
            source_revision="r1",
            expected_manifest_sha256=self.manifest(first),
        )
        installer.install(
            artifact=second,
            runtime_version="2",
            source_revision="r2",
            expected_manifest_sha256=self.manifest(second),
        )

        result = installer.rollback()

        self.assertEqual(
            result["status"],
            "rolled-back",
        )
        self.assertIn(
            "v1",
            self.marker(
                self.umbrel / "seymour-runtime"
            ),
        )
        self.assertIn(
            "v2",
            self.marker(
                self.umbrel
                / "seymour-runtime.previous"
            ),
        )

    def test_corrupt_artifact_is_rejected_without_promotion(self):
        artifact = make_runtime(
            self.artifacts,
            "bad",
        )
        (
            artifact
            / "scripts/seymour-blockchain-install"
        ).unlink()

        with self.assertRaises(
            MODULE.RuntimeInstallError
        ):
            self.installer().install(
                artifact=artifact,
                runtime_version="bad",
                source_revision="bad",
                expected_manifest_sha256=(
                    self.manifest(artifact)
                ),
            )

        self.assertFalse(
            (self.umbrel / "seymour-runtime").exists()
        )

    def test_failed_promoted_verification_restores_previous(self):
        first = make_runtime(
            self.artifacts,
            "v1",
        )
        second = make_runtime(
            self.artifacts,
            "v2",
        )

        normal = self.installer()
        normal.install(
            artifact=first,
            runtime_version="1",
            source_revision="r1",
            expected_manifest_sha256=self.manifest(first),
        )

        calls = {"current": 0}

        def verifier(path: Path):
            MODULE.verify_runtime(path)

            if path == self.umbrel / "seymour-runtime":
                calls["current"] += 1
                raise MODULE.RuntimeInstallError(
                    "injected promoted verification failure"
                )

        failing = self.installer(verifier)

        with self.assertRaises(
            MODULE.RuntimeInstallError
        ):
            failing.install(
                artifact=second,
                runtime_version="2",
                source_revision="r2",
                expected_manifest_sha256=self.manifest(second),
            )

        self.assertGreater(
            calls["current"],
            0,
        )
        self.assertIn(
            "v1",
            self.marker(
                self.umbrel / "seymour-runtime"
            ),
        )

    def test_lock_contention_fails_closed(self):
        installer = self.installer()
        installer._prepare()

        with installer.paths.lock.open("a+") as handle:
            fcntl.flock(
                handle.fileno(),
                fcntl.LOCK_EX | fcntl.LOCK_NB,
            )

            artifact = make_runtime(
                self.artifacts,
                "v1",
            )

            with self.assertRaisesRegex(
                MODULE.RuntimeInstallError,
                "already in progress",
            ):
                installer.install(
                    artifact=artifact,
                    runtime_version="1",
                    source_revision="r1",
                    expected_manifest_sha256=self.manifest(artifact),
                )

    def test_evidence_is_written_and_current_matches_history(self):
        artifact = make_runtime(
            self.artifacts,
            "v1",
        )

        result = self.installer().install(
            artifact=artifact,
            runtime_version="1",
            source_revision="r1",
            expected_manifest_sha256=self.manifest(artifact),
        )

        current = json.loads(
            (
                self.umbrel
                / "seymour-evidence"
                / "blockchain-target-runtime"
                / "current.json"
            ).read_text(encoding="utf-8")
        )

        history = json.loads(
            (
                self.umbrel
                / "seymour-evidence"
                / "blockchain-target-runtime"
                / "history"
                / f"{result['operationId']}.json"
            ).read_text(encoding="utf-8")
        )

        self.assertEqual(current, history)
        self.assertEqual(
            current["contract"],
            MODULE.CONTRACT,
        )
        self.assertEqual(
            current["sourceRevision"],
            "r1",
        )
        self.assertTrue(
            current["payloadManifestSha256"]
        )

    def test_source_file_modes_are_preserved(self):
        artifact = make_runtime(
            self.artifacts,
            "v1",
        )

        executable = (
            artifact
            / "scripts/seymour-blockchain-install"
        )
        executable.chmod(0o751)

        self.installer().install(
            artifact=artifact,
            runtime_version="1",
            source_revision="r1",
            expected_manifest_sha256=self.manifest(artifact),
        )

        installed = (
            self.umbrel
            / "seymour-runtime"
            / "scripts/seymour-blockchain-install"
        )

        self.assertEqual(
            stat.S_IMODE(installed.stat().st_mode),
            0o751,
        )

    def test_wrong_reviewed_manifest_rejected_before_promotion(self):
        artifact = make_runtime(
            self.artifacts,
            "v1",
        )

        with self.assertRaisesRegex(
            MODULE.RuntimeInstallError,
            "reviewed payload manifest",
        ):
            self.installer().install(
                artifact=artifact,
                runtime_version="1",
                source_revision="r1",
                expected_manifest_sha256="0" * 64,
            )

        self.assertFalse(
            (self.umbrel / "seymour-runtime").exists()
        )

    def test_invalid_expected_manifest_is_rejected(self):
        artifact = make_runtime(
            self.artifacts,
            "v1",
        )

        with self.assertRaisesRegex(
            MODULE.RuntimeInstallError,
            "SHA-256 is invalid",
        ):
            self.installer().install(
                artifact=artifact,
                runtime_version="1",
                source_revision="r1",
                expected_manifest_sha256="not-a-sha",
            )

        self.assertFalse(
            (self.umbrel / "seymour-runtime").exists()
        )

    def test_failed_explicit_rollback_restores_original_current(self):
        first = make_runtime(
            self.artifacts,
            "v1",
        )
        second = make_runtime(
            self.artifacts,
            "v2",
        )

        normal = self.installer()

        normal.install(
            artifact=first,
            runtime_version="1",
            source_revision="r1",
            expected_manifest_sha256=self.manifest(first),
        )

        normal.install(
            artifact=second,
            runtime_version="2",
            source_revision="r2",
            expected_manifest_sha256=self.manifest(second),
        )

        def verifier(path: Path):
            MODULE.verify_runtime(path)

            if (
                path == self.umbrel / "seymour-runtime"
                and "v1" in self.marker(path)
            ):
                raise MODULE.RuntimeInstallError(
                    "injected rollback verification failure"
                )

        failing = self.installer(verifier)

        with self.assertRaises(
            MODULE.RuntimeInstallError
        ):
            failing.rollback()

        self.assertIn(
            "v2",
            self.marker(
                self.umbrel / "seymour-runtime"
            ),
        )


    def test_failed_update_preserves_current_evidence(self):
        first = make_runtime(
            self.artifacts,
            "v1",
        )
        second = make_runtime(
            self.artifacts,
            "v2",
        )

        normal = self.installer()

        installed = normal.install(
            artifact=first,
            runtime_version="1",
            source_revision="r1",
            expected_manifest_sha256=self.manifest(first),
        )

        current_path = (
            self.umbrel
            / "seymour-evidence"
            / "blockchain-target-runtime"
            / "current.json"
        )

        before = json.loads(
            current_path.read_text(encoding="utf-8")
        )

        def verifier(path: Path):
            MODULE.verify_runtime(path)

            if (
                path == self.umbrel / "seymour-runtime"
                and "v2" in self.marker(path)
            ):
                raise MODULE.RuntimeInstallError(
                    "injected promoted verification failure"
                )

        failing = self.installer(verifier)

        with self.assertRaises(
            MODULE.RuntimeInstallError
        ):
            failing.install(
                artifact=second,
                runtime_version="2",
                source_revision="r2",
                expected_manifest_sha256=self.manifest(second),
            )

        after = json.loads(
            current_path.read_text(encoding="utf-8")
        )

        self.assertEqual(
            installed["operationId"],
            before["operationId"],
        )
        self.assertEqual(before, after)
        self.assertEqual(after["status"], "installed")

        history_root = (
            self.umbrel
            / "seymour-evidence"
            / "blockchain-target-runtime"
            / "history"
        )

        records = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in history_root.glob("*.json")
        ]

        self.assertEqual(len(records), 2)
        self.assertEqual(
            sorted(record["status"] for record in records),
            ["failed", "installed"],
        )

    def test_failed_fresh_install_has_history_but_no_current(self):
        artifact = make_runtime(
            self.artifacts,
            "v1",
        )

        def verifier(path: Path):
            MODULE.verify_runtime(path)

            if path == self.umbrel / "seymour-runtime":
                raise MODULE.RuntimeInstallError(
                    "injected fresh promotion failure"
                )

        failing = self.installer(verifier)

        with self.assertRaises(
            MODULE.RuntimeInstallError
        ):
            failing.install(
                artifact=artifact,
                runtime_version="1",
                source_revision="r1",
                expected_manifest_sha256=self.manifest(artifact),
            )

        evidence_root = (
            self.umbrel
            / "seymour-evidence"
            / "blockchain-target-runtime"
        )

        self.assertFalse(
            (evidence_root / "current.json").exists()
        )

        records = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in (evidence_root / "history").glob("*.json")
        ]

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["status"], "failed")

    def test_failed_explicit_rollback_writes_history_only(self):
        first = make_runtime(
            self.artifacts,
            "v1",
        )
        second = make_runtime(
            self.artifacts,
            "v2",
        )

        normal = self.installer()

        normal.install(
            artifact=first,
            runtime_version="1",
            source_revision="r1",
            expected_manifest_sha256=self.manifest(first),
        )

        installed = normal.install(
            artifact=second,
            runtime_version="2",
            source_revision="r2",
            expected_manifest_sha256=self.manifest(second),
        )

        current_path = (
            self.umbrel
            / "seymour-evidence"
            / "blockchain-target-runtime"
            / "current.json"
        )

        before = json.loads(
            current_path.read_text(encoding="utf-8")
        )

        def verifier(path: Path):
            MODULE.verify_runtime(path)

            if (
                path == self.umbrel / "seymour-runtime"
                and "v1" in self.marker(path)
            ):
                raise MODULE.RuntimeInstallError(
                    "injected rollback verification failure"
                )

        failing = self.installer(verifier)

        with self.assertRaises(
            MODULE.RuntimeInstallError
        ):
            failing.rollback()

        after = json.loads(
            current_path.read_text(encoding="utf-8")
        )

        self.assertEqual(
            installed["operationId"],
            before["operationId"],
        )
        self.assertEqual(before, after)

        history_root = (
            self.umbrel
            / "seymour-evidence"
            / "blockchain-target-runtime"
            / "history"
        )

        records = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in history_root.glob("*.json")
        ]

        self.assertEqual(len(records), 3)

        rollback_failures = [
            record
            for record in records
            if (
                record["operation"] == "rollback"
                and record["status"] == "failed"
            )
        ]

        self.assertEqual(len(rollback_failures), 1)


    def test_no_target_root_is_exposed_by_public_cli(self):
        text = (
            PACKAGE / "scripts/install.py"
        ).read_text(encoding="utf-8")

        self.assertNotIn(
            "--umbrel-root",
            text,
        )
        self.assertNotIn(
            "--target-root",
            text,
        )
        self.assertNotIn(
            "--command",
            text,
        )
        self.assertNotIn(
            "--shell",
            text,
        )
        self.assertNotIn(
            "--argv",
            text,
        )


if __name__ == "__main__":
    unittest.main()
