#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]
ROOT = PACKAGE / "build" / "seymour-runtime"

REQUIRED = (
    "scripts/seymour-blockchain-install",
    "scripts/seymour-install-btc",
    "scripts/seymour-install-bch",
    "scripts/seymour-install-monero",
    "scripts/seymour-umbrel-app",
    "scripts/seymour-umbrel-runtime",
    "shared/provider_catalog/providers.v1.json",
    "shared/umbrel_control/native-client.ts",
    "shared/bch_install/workflow.py",
    "shared/umbrel_runtime/cli.py",
    "shared/blockchain_install/umbrel_runtime.py",
    "seymour-bitcoin-node/umbrel-app.yml",
    "seymour-bitcoin-node/docker-compose.yml",
    "seymour-bitcoin-node/hooks/pre-install",
    "seymour-bch-node/umbrel-app.yml",
    "seymour-bch-node/docker-compose.yml",
    "seymour-bch-node/hooks/pre-install",
    "seymour-monero-node/umbrel-app.yml",
    "seymour-monero-node/docker-compose.yml",
    "seymour-monero-node/hooks/pre-install",
)


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


for relative in REQUIRED:
    if not (ROOT / relative).is_file():
        fail(f"missing {relative}")

for forbidden in (
    "seymour-blockchain-manager",
    "nexus-command-center",
    "packages",
    "tests",
    ".git",
):
    if (ROOT / forbidden).exists():
        fail(f"forbidden payload path: {forbidden}")

catalog = json.loads(
    (
        ROOT
        / "shared/provider_catalog/providers.v1.json"
    ).read_text()
)

if not isinstance(catalog, dict):
    fail("provider catalog is invalid")

for executable in (
    "scripts/seymour-blockchain-install",
    "scripts/seymour-install-btc",
    "scripts/seymour-install-bch",
    "scripts/seymour-install-monero",
    "scripts/seymour-umbrel-app",
    "scripts/seymour-umbrel-runtime",
):
    path = ROOT / executable
    if not (path.stat().st_mode & 0o111):
        fail(f"not executable: {executable}")

environment = dict(os.environ)
environment["PYTHONDONTWRITEBYTECODE"] = "1"

result = subprocess.run(
    [
        str(ROOT / "scripts/seymour-blockchain-install"),
        "--help",
    ],
    cwd=ROOT,
    env=environment,
    text=True,
    capture_output=True,
    check=False,
)

if result.returncode != 0:
    fail(
        "target CLI cannot load from packaged runtime: "
        + result.stderr.strip()
    )

help_text = result.stdout + result.stderr

for required in (
    "--provider-id",
    "--storage-target-id",
    "--execute",
):
    if required not in help_text:
        fail(f"CLI missing fixed input: {required}")

for forbidden in (
    "--command",
    "--shell",
    "--argv",
    "--password",
    "--rpc-password",
    "--remote-targets-path",
    "--umbrel-data-directory",
):
    if forbidden in help_text:
        fail(f"forbidden CLI input exposed: {forbidden}")

print("targetRuntimePackage=PASS")
