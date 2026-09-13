from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "seymour-blockchain-manager" / "hooks" / "pre-update"


class BlockchainManagerUpdatePayloadTests(unittest.TestCase):
    def _fixture(self) -> tuple[Path, Path, Path]:
        root = Path(tempfile.mkdtemp(prefix="seymour-update-hook-"))
        source = root / "repo" / "seymour-blockchain-manager"
        target = root / "umbrel" / "app-data" / "seymour-blockchain-manager"

        for component in ("catalog", "control", "shared", "web"):
            (source / "data" / component).mkdir(parents=True, exist_ok=True)

        target.mkdir(parents=True, exist_ok=True)
        return root, source, target

    def _run(self, source: Path, target: Path) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["SCRIPT_APP_REPO_DIR"] = str(source)
        env["APP_DATA_DIR"] = str(target)

        return subprocess.run(
            [str(HOOK)],
            env=env,
            text=True,
            capture_output=True,
            check=False,
            timeout=15,
        )

    def test_syncs_release_owned_payload_and_preserves_persistent_state(self) -> None:
        root, source, target = self._fixture()
        try:
            (source / "data" / "web" / "app.py").write_text(
                "published\n",
                encoding="utf-8",
            )
            (source / "data" / "control" / "tool").write_text(
                "#!/bin/sh\nexit 0\n",
                encoding="utf-8",
            )
            (source / "data" / "control" / "tool").chmod(0o755)
            (source / "data" / "shared" / "engine.py").write_text(
                "new\n",
                encoding="utf-8",
            )
            (source / "data" / "catalog" / "providers.json").write_text(
                "{}\n",
                encoding="utf-8",
            )

            (target / "data" / "web").mkdir(parents=True)
            (target / "data" / "web" / "app.py").write_text(
                "old\n",
                encoding="utf-8",
            )

            for persistent in ("private", "evidence", "runtime-evidence", "backups"):
                directory = target / "data" / persistent
                directory.mkdir(parents=True)
                (directory / "sentinel").write_text(
                    persistent,
                    encoding="utf-8",
                )

            result = self._run(source, target)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                (target / "data" / "web" / "app.py").read_text(encoding="utf-8"),
                "published\n",
            )
            self.assertTrue(target.joinpath("data/control/tool").exists())
            self.assertEqual(
                target.joinpath("data/control/tool").stat().st_mode & 0o777,
                0o755,
            )
            self.assertTrue(target.joinpath("data/shared/engine.py").exists())
            self.assertTrue(target.joinpath("data/catalog/providers.json").exists())

            for persistent in ("private", "evidence", "runtime-evidence", "backups"):
                sentinel = target / "data" / persistent / "sentinel"
                self.assertEqual(
                    sentinel.read_text(encoding="utf-8"),
                    persistent,
                )
        finally:
            shutil.rmtree(root)

    def test_does_not_delete_target_only_files_inside_release_directories(self) -> None:
        root, source, target = self._fixture()
        try:
            (source / "data" / "web" / "app.py").write_text(
                "published\n",
                encoding="utf-8",
            )

            target_web = target / "data" / "web"
            target_web.mkdir(parents=True)
            (target_web / "legacy-local-file").write_text(
                "preserve\n",
                encoding="utf-8",
            )

            result = self._run(source, target)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                (target_web / "legacy-local-file").read_text(encoding="utf-8"),
                "preserve\n",
            )
        finally:
            shutil.rmtree(root)

    def test_fails_closed_without_required_environment(self) -> None:
        env = os.environ.copy()
        env.pop("SCRIPT_APP_REPO_DIR", None)
        env.pop("APP_DATA_DIR", None)

        result = subprocess.run(
            [str(HOOK)],
            env=env,
            text=True,
            capture_output=True,
            check=False,
            timeout=15,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SCRIPT_APP_REPO_DIR is not set", result.stderr)


if __name__ == "__main__":
    unittest.main()
