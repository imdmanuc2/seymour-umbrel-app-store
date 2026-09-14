from __future__ import annotations

import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
APP_ID = "seymour-blockchain-manager"
HOOK = REPOSITORY_ROOT / APP_ID / "hooks" / "pre-update"


class BlockchainManagerTlsPrivateDirectoryTests(unittest.TestCase):
    def make_fixture(self):
        root = Path(tempfile.mkdtemp(prefix="seymour-bm-tls-test-"))

        app_root = root / APP_ID
        hook_dir = app_root / "hooks"
        private_dir = app_root / "data" / "private"

        release_root = root / "release" / APP_ID

        for component in ("catalog", "control", "shared", "web"):
            (release_root / "data" / component).mkdir(
                parents=True,
                exist_ok=True,
            )

        hook_dir.mkdir(parents=True, exist_ok=True)
        private_dir.mkdir(parents=True, exist_ok=True)

        installed_hook = hook_dir / "pre-update"
        shutil.copy2(HOOK, installed_hook)
        installed_hook.chmod(0o755)

        self.addCleanup(shutil.rmtree, root, ignore_errors=True)

        return app_root, release_root, installed_hook

    def run_hook(
        self,
        app_root: Path,
        release_root: Path,
        installed_hook: Path,
    ):
        env = os.environ.copy()
        env["APP_DATA_DIR"] = str(app_root)
        env["SCRIPT_APP_REPO_DIR"] = str(release_root)

        return subprocess.run(
            ["bash", str(installed_hook)],
            cwd=installed_hook.parent,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_prepares_tls_directory_with_app_root_ownership_and_mode_0700(self):
        app_root, release_root, installed_hook = self.make_fixture()

        tls_dir = (
            app_root
            / "data"
            / "private"
            / "nexus-control-tls"
        )

        # Simulate a pre-existing Docker-created bind source with an
        # overly broad mode. In the portable unit fixture ownership is
        # already the current test account; the hook must derive owner
        # from the installed app root and normalize the mode.
        tls_dir.mkdir(parents=True)
        tls_dir.chmod(0o755)

        app_stat = app_root.stat()

        result = self.run_hook(
            app_root,
            release_root,
            installed_hook,
        )

        self.assertEqual(
            result.returncode,
            0,
            result.stderr,
        )

        tls_stat = tls_dir.stat()

        self.assertEqual(
            tls_stat.st_uid,
            app_stat.st_uid,
        )
        self.assertEqual(
            tls_stat.st_gid,
            app_stat.st_gid,
        )
        self.assertEqual(
            stat.S_IMODE(tls_stat.st_mode),
            0o700,
        )

    def test_creates_missing_tls_directory_with_mode_0700(self):
        app_root, release_root, installed_hook = self.make_fixture()

        tls_dir = (
            app_root
            / "data"
            / "private"
            / "nexus-control-tls"
        )

        self.assertFalse(tls_dir.exists())

        app_stat = app_root.stat()

        result = self.run_hook(
            app_root,
            release_root,
            installed_hook,
        )

        self.assertEqual(
            result.returncode,
            0,
            result.stderr,
        )
        self.assertTrue(tls_dir.is_dir())

        tls_stat = tls_dir.stat()

        self.assertEqual(
            tls_stat.st_uid,
            app_stat.st_uid,
        )
        self.assertEqual(
            tls_stat.st_gid,
            app_stat.st_gid,
        )
        self.assertEqual(
            stat.S_IMODE(tls_stat.st_mode),
            0o700,
        )

    def test_rejects_tls_path_symlink(self):
        app_root, release_root, installed_hook = self.make_fixture()

        tls_dir = (
            app_root
            / "data"
            / "private"
            / "nexus-control-tls"
        )

        outside = app_root.parent / "outside-tls-target"
        outside.mkdir()

        tls_dir.symlink_to(
            outside,
            target_is_directory=True,
        )

        result = self.run_hook(
            app_root,
            release_root,
            installed_hook,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "TLS private directory must not be a symlink",
            result.stderr,
        )


if __name__ == "__main__":
    unittest.main()
