#!/usr/bin/env python3
from __future__ import annotations

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
