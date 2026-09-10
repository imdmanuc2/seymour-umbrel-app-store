#!/usr/bin/env python3
from __future__ import annotations

import gzip
import hashlib
import io
import json
import shutil
import tarfile
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]
PACKAGES_ROOT = PACKAGE.parent

BOOTSTRAP_SOURCE = PACKAGE / "scripts" / "bootstrap.py"

INSTALLER_SOURCE = (
    PACKAGES_ROOT
    / "SBP-077.1-Shared-Blockchain-Target-Runtime-Installer"
    / "scripts"
    / "runtime_installer.py"
)

BUILD_ROOT = PACKAGE / "build"
STAGE_ROOT = BUILD_ROOT / "seymour-bootstrap"

ARCHIVE = BUILD_ROOT / "seymour-bootstrap.tar.gz"
METADATA = BUILD_ROOT / "seymour-bootstrap.artifact.json"

ARTIFACT_TYPE = "seymour-blockchain-target-bootstrap"
ARTIFACT_VERSION = "1.0.0"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)

            if not chunk:
                break

            digest.update(chunk)

    return digest.hexdigest()


def source_files() -> tuple[tuple[str, Path, int], ...]:
    return (
        (
            "bootstrap.py",
            BOOTSTRAP_SOURCE,
            0o755,
        ),
        (
            "runtime_installer.py",
            INSTALLER_SOURCE,
            0o644,
        ),
    )


def validate_sources() -> None:
    for name, source, _mode in source_files():
        if not source.is_file():
            raise RuntimeError(
                f"bootstrap source missing: {name}"
            )


def stage() -> None:
    if BUILD_ROOT.exists():
        shutil.rmtree(BUILD_ROOT)

    STAGE_ROOT.mkdir(parents=True)

    for name, source, mode in source_files():
        destination = STAGE_ROOT / name
        shutil.copyfile(source, destination)
        destination.chmod(mode)


def build_archive() -> None:
    buffer = io.BytesIO()

    with tarfile.open(
        fileobj=buffer,
        mode="w",
        format=tarfile.PAX_FORMAT,
    ) as handle:
        for name, source, mode in source_files():
            data = source.read_bytes()

            info = tarfile.TarInfo(
                f"seymour-bootstrap/{name}"
            )

            info.size = len(data)
            info.uid = 0
            info.gid = 0
            info.uname = ""
            info.gname = ""
            info.mtime = 0
            info.mode = mode

            handle.addfile(
                info,
                io.BytesIO(data),
            )

    with ARCHIVE.open("wb") as raw:
        with gzip.GzipFile(
            filename="",
            mode="wb",
            fileobj=raw,
            mtime=0,
        ) as compressed:
            compressed.write(buffer.getvalue())


def write_metadata() -> dict:
    files = []

    for name, source, mode in source_files():
        files.append(
            {
                "path": name,
                "sha256": sha256_file(source),
                "mode": f"{mode:04o}",
            }
        )

    payload = {
        "schemaVersion": 1,
        "artifactType": ARTIFACT_TYPE,
        "artifactVersion": ARTIFACT_VERSION,
        "archiveFile": ARCHIVE.name,
        "archiveSha256": sha256_file(ARCHIVE),
        "archiveFormat": "tar.gz",
        "rootDirectory": "seymour-bootstrap",
        "fileCount": len(files),
        "files": files,
    }

    METADATA.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return payload


def main() -> int:
    validate_sources()
    stage()
    build_archive()
    metadata = write_metadata()

    print(
        json.dumps(
            {
                "success": True,
                "archive": str(ARCHIVE),
                "archiveSha256": metadata[
                    "archiveSha256"
                ],
                "fileCount": metadata["fileCount"],
            },
            sort_keys=True,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
