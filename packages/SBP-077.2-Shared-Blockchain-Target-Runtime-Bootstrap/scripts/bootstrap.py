#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import stat
import sys
import tarfile
import tempfile
from pathlib import Path
from types import ModuleType


DEFAULT_UMBREL_ROOT = Path("/home/umbrel/umbrel")

_SHA256_HEX = frozenset("0123456789abcdef")


class RuntimeBootstrapError(RuntimeError):
    pass


def normalize_sha256(value: str, name: str) -> str:
    normalized = str(value or "").strip().lower()

    if (
        len(normalized) != 64
        or any(ch not in _SHA256_HEX for ch in normalized)
    ):
        raise RuntimeBootstrapError(
            f"{name} is invalid"
        )

    return normalized


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)

            if not chunk:
                break

            digest.update(chunk)

    return digest.hexdigest()


def validate_archive_member(member: tarfile.TarInfo) -> None:
    name = member.name

    if not (
        name == "seymour-runtime"
        or name.startswith("seymour-runtime/")
    ):
        raise RuntimeBootstrapError(
            f"archive contains invalid root member: {name}"
        )

    path = Path(name)

    if path.is_absolute() or ".." in path.parts:
        raise RuntimeBootstrapError(
            f"archive contains unsafe path: {name}"
        )

    if member.issym() or member.islnk():
        raise RuntimeBootstrapError(
            f"archive links are prohibited: {name}"
        )

    if member.isdev() or member.isfifo():
        raise RuntimeBootstrapError(
            f"archive special files are prohibited: {name}"
        )

    if not (member.isfile() or member.isdir()):
        raise RuntimeBootstrapError(
            f"archive member type is unsupported: {name}"
        )

    if member.mode & ~0o777:
        raise RuntimeBootstrapError(
            f"archive special permission bits are prohibited: {name}"
        )


def safe_extract(
    archive: Path,
    destination: Path,
) -> Path:
    with tarfile.open(archive, "r:gz") as handle:
        members = handle.getmembers()

        if not members:
            raise RuntimeBootstrapError(
                "runtime archive is empty"
            )

        for member in members:
            validate_archive_member(member)

        roots = {
            Path(member.name).parts[0]
            for member in members
            if Path(member.name).parts
        }

        if roots != {"seymour-runtime"}:
            raise RuntimeBootstrapError(
                "runtime archive must contain exactly one runtime root"
            )

        for member in members:
            target = destination / member.name

            resolved_parent = target.parent.resolve()
            destination_root = destination.resolve()

            if (
                resolved_parent != destination_root
                and destination_root not in resolved_parent.parents
            ):
                raise RuntimeBootstrapError(
                    f"archive extraction escaped staging: {member.name}"
                )

        handle.extractall(
            destination,
            members=members,
            filter="data",
        )

        # Python's data extraction filter intentionally sanitizes
        # permissions. The SBP-077.1 trust manifest includes exact
        # file modes, so restore only the already-validated standard
        # permission bits from the reviewed archive metadata.
        for member in members:
            target = destination / member.name

            if member.isfile() or member.isdir():
                os.chmod(
                    target,
                    stat.S_IMODE(member.mode),
                )

    runtime = destination / "seymour-runtime"

    if not runtime.is_dir():
        raise RuntimeBootstrapError(
            "extracted runtime root is missing"
        )

    return runtime


def load_installer_module(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "sbp0771_runtime_installer",
        path,
    )

    if spec is None or spec.loader is None:
        raise RuntimeBootstrapError(
            "unable to load runtime installer"
        )

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    return module


class RuntimeBootstrap:
    def __init__(
        self,
        *,
        umbrel_root: Path = DEFAULT_UMBREL_ROOT,
        installer_module_path: Path | None = None,
    ) -> None:
        if not umbrel_root.is_absolute():
            raise ValueError(
                "Umbrel root must be absolute"
            )

        self.umbrel_root = umbrel_root
        self.installer_module_path = (
            installer_module_path
            or Path(__file__).resolve().with_name(
                "runtime_installer.py"
            )
        )

    def install(
        self,
        *,
        archive: Path,
        archive_sha256: str,
        payload_manifest_sha256: str,
        runtime_version: str,
        source_revision: str,
    ) -> dict:
        archive = Path(archive)

        if not archive.is_file():
            raise RuntimeBootstrapError(
                "runtime archive is not a regular file"
            )

        expected_archive_sha = normalize_sha256(
            archive_sha256,
            "archive SHA-256",
        )

        expected_payload_sha = normalize_sha256(
            payload_manifest_sha256,
            "payload manifest SHA-256",
        )

        actual_archive_sha = file_sha256(archive)

        if actual_archive_sha != expected_archive_sha:
            raise RuntimeBootstrapError(
                "runtime archive does not match reviewed SHA-256"
            )

        installer_module = load_installer_module(
            self.installer_module_path
        )

        extraction_root = Path(
            tempfile.mkdtemp(
                prefix=".seymour-runtime.extract.",
                dir=str(self.umbrel_root),
            )
        )

        try:
            runtime = safe_extract(
                archive,
                extraction_root,
            )

            installer_module.verify_runtime(runtime)

            actual_payload_sha, _ = (
                installer_module.payload_manifest(runtime)
            )

            if actual_payload_sha != expected_payload_sha:
                raise RuntimeBootstrapError(
                    "extracted runtime manifest does not match reviewed payload manifest"
                )

            installer = installer_module.RuntimeInstaller(
                umbrel_root=self.umbrel_root,
            )

            result = installer.install(
                artifact=runtime,
                runtime_version=str(runtime_version).strip(),
                source_revision=str(source_revision).strip(),
                expected_manifest_sha256=expected_payload_sha,
            )

            return {
                "success": True,
                "archiveSha256": actual_archive_sha,
                "payloadManifestSha256": actual_payload_sha,
                "runtimeVersion": str(runtime_version).strip(),
                "sourceRevision": str(source_revision).strip(),
                "installer": result,
            }
        finally:
            shutil.rmtree(
                extraction_root,
                ignore_errors=True,
            )


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(
        description=(
            "Safely bootstrap a verified Seymour blockchain target runtime bundle."
        )
    )

    value.add_argument(
        "--archive",
        required=True,
        type=Path,
    )
    value.add_argument(
        "--archive-sha256",
        required=True,
    )
    value.add_argument(
        "--payload-manifest-sha256",
        required=True,
    )
    value.add_argument(
        "--runtime-version",
        required=True,
    )
    value.add_argument(
        "--source-revision",
        required=True,
    )

    return value


def main() -> int:
    args = parser().parse_args()

    try:
        result = RuntimeBootstrap().install(
            archive=args.archive,
            archive_sha256=args.archive_sha256,
            payload_manifest_sha256=args.payload_manifest_sha256,
            runtime_version=args.runtime_version,
            source_revision=args.source_revision,
        )
    except Exception as exc:
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
            result,
            sort_keys=True,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
