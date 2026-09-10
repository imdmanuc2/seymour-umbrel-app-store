from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]


def main() -> int:
    manifest = json.loads(
        (PACKAGE / "package.json").read_text(
            encoding="utf-8"
        )
    )

    assert manifest["id"] == "SBP-077.2"
    assert manifest["deployment"] == "target-local"

    bootstrap = PACKAGE / "scripts/bootstrap.py"
    builder = PACKAGE / "scripts/build.py"

    assert bootstrap.is_file()
    assert bootstrap.stat().st_mode & 0o111

    assert builder.is_file()
    assert builder.stat().st_mode & 0o111

    result = subprocess.run(
        [
            sys.executable,
            str(bootstrap),
            "--help",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0

    help_text = result.stdout + result.stderr

    required = (
        "--archive",
        "--archive-sha256",
        "--payload-manifest-sha256",
        "--runtime-version",
        "--source-revision",
    )

    forbidden = (
        "--target-root",
        "--umbrel-root",
        "--command",
        "--shell",
        "--argv",
        "--password",
        "--rpc-password",
    )

    for item in required:
        assert item in help_text

    for item in forbidden:
        assert item not in help_text

    print("SBP0772Package=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
