#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]

result = subprocess.run(
    [
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        str(PACKAGE / "tests"),
        "-p",
        "test_runtime_installer.py",
        "-v",
    ],
    text=True,
    check=False,
)

raise SystemExit(result.returncode)
