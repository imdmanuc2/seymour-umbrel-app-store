#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from runtime_installer import (
    RuntimeInstallError,
    RuntimeInstaller,
)


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(
        description=(
            "Install or roll back the shared Seymour "
            "blockchain target runtime."
        )
    )

    subparsers = value.add_subparsers(
        dest="operation",
        required=True,
    )

    install = subparsers.add_parser("install")
    install.add_argument(
        "--artifact",
        required=True,
        type=Path,
    )
    install.add_argument(
        "--runtime-version",
        required=True,
    )
    install.add_argument(
        "--source-revision",
        required=True,
    )
    install.add_argument(
        "--payload-manifest-sha256",
        required=True,
    )

    subparsers.add_parser("rollback")

    return value


def main() -> int:
    args = parser().parse_args()
    installer = RuntimeInstaller()

    try:
        if args.operation == "install":
            result = installer.install(
                artifact=args.artifact,
                runtime_version=args.runtime_version,
                source_revision=args.source_revision,
                expected_manifest_sha256=(
                    args.payload_manifest_sha256
                ),
            )
        else:
            result = installer.rollback()
    except RuntimeInstallError as exc:
        print(
            json.dumps(
                {
                    "success": False,
                    "error": str(exc),
                },
                sort_keys=True,
            )
        )
        return 1

    print(
        json.dumps(
            {
                "success": True,
                "result": result,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
