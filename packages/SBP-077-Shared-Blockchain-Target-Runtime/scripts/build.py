#!/usr/bin/env python3
from __future__ import annotations

import shutil
import sys
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[3]
PACKAGE = Path(__file__).resolve().parents[1]
OUTPUT = PACKAGE / "build" / "seymour-runtime"

FILES = (
    "scripts/seymour-blockchain-install",
    "scripts/seymour-install-btc",
    "scripts/seymour-install-bch",
    "scripts/seymour-install-monero",
    "scripts/seymour-umbrel-app",
    "scripts/seymour-umbrel-runtime",
    "shared/provider_catalog/providers.v1.json",
    "shared/umbrel_control/__init__.py",
    "shared/umbrel_control/bridge.py",
    "shared/umbrel_control/http_client.py",
    "shared/umbrel_control/native-client.ts",
)

TREES = (
    "shared/blockchain_install",
    "shared/bch_install",
    "shared/umbrel_runtime",
)

APP_FILES = (
    "umbrel-app.yml",
    "docker-compose.yml",
    "hooks/pre-install",
)

APPS = (
    "seymour-bitcoin-node",
    "seymour-bch-node",
    "seymour-monero-node",
)


def copy_file(relative: str) -> None:
    source = REPOSITORY / relative
    destination = OUTPUT / relative

    if not source.is_file():
        raise RuntimeError(
            f"Required runtime file is missing: {relative}"
        )

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    shutil.copy2(source, destination)


def copy_tree(relative: str) -> None:
    source = REPOSITORY / relative
    destination = OUTPUT / relative

    if not source.is_dir():
        raise RuntimeError(
            f"Required runtime tree is missing: {relative}"
        )

    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns(
            "__pycache__",
            "*.pyc",
            "*.pyo",
        ),
    )


def main() -> int:
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)

    OUTPUT.mkdir(
        parents=True,
        exist_ok=False,
    )

    for relative in FILES:
        copy_file(relative)

    for relative in TREES:
        copy_tree(relative)

    for app in APPS:
        for filename in APP_FILES:
            copy_file(
                f"{app}/{filename}"
            )

    for cache in sorted(
        OUTPUT.rglob("__pycache__"),
        reverse=True,
    ):
        if cache.is_dir():
            shutil.rmtree(cache)

    for bytecode in OUTPUT.rglob("*.py[co]"):
        if bytecode.is_file():
            bytecode.unlink()

    print(OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
