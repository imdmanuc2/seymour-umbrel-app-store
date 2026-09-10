#!/usr/bin/env python3
from __future__ import annotations

import gzip
import hashlib
import io
import json
import shutil
import stat
import subprocess
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[3]
PACKAGE = Path(__file__).resolve().parents[1]

BUILD = PACKAGE / "build"
OUTPUT = BUILD / "seymour-runtime"
ARCHIVE = BUILD / "seymour-runtime.tar.gz"
METADATA = BUILD / "seymour-runtime.artifact.json"

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

RUNTIME_VERSION = "1.0.0"


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


def clean_generated_junk() -> None:
    for cache in sorted(
        OUTPUT.rglob("__pycache__"),
        reverse=True,
    ):
        if cache.is_dir():
            shutil.rmtree(cache)

    for bytecode in OUTPUT.rglob("*.py[co]"):
        if bytecode.is_file():
            bytecode.unlink()


def source_revision() -> str:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(REPOSITORY),
            "rev-parse",
            "HEAD",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    revision = result.stdout.strip()

    if result.returncode != 0 or len(revision) != 40:
        raise RuntimeError(
            "Unable to determine reviewed source revision"
        )

    return revision


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)

            if not chunk:
                break

            digest.update(chunk)

    return digest.hexdigest()


def installer_payload_manifest(
    root: Path,
) -> tuple[str, list[dict[str, object]]]:
    """
    Mirror SBP-077.1 payload trust semantics:
    regular files, relative path, SHA-256, and executable mode.
    """

    entries: list[dict[str, object]] = []

    for path in sorted(
        (
            item
            for item in root.rglob("*")
            if item.is_file()
        ),
        key=lambda item: item.relative_to(root).as_posix(),
    ):
        relative = path.relative_to(root).as_posix()
        mode = stat.S_IMODE(path.stat().st_mode)

        entries.append(
            {
                "path": relative,
                "sha256": file_sha256(path),
                "mode": f"{mode:04o}",
            }
        )

    encoded = json.dumps(
        entries,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest(), entries


def _tar_header(
    *,
    name: str,
    mode: int,
    size: int,
    typeflag: bytes,
) -> bytes:
    header = bytearray(512)

    def field(
        offset: int,
        length: int,
        value: bytes,
    ) -> None:
        if len(value) > length:
            raise RuntimeError(
                f"tar header value too long: {name}"
            )

        header[offset:offset + length] = (
            value + b"\0" * (length - len(value))
        )

    field(0, 100, name.encode("utf-8"))
    field(100, 8, f"{mode:07o}\0".encode())
    field(108, 8, b"0000000\0")
    field(116, 8, b"0000000\0")
    field(124, 12, f"{size:011o}\0".encode())
    field(136, 12, b"00000000000\0")

    header[148:156] = b"        "
    header[156:157] = typeflag

    field(257, 6, b"ustar\0")
    field(263, 2, b"00")

    checksum = sum(header)
    header[148:156] = (
        f"{checksum:06o}\0 ".encode("ascii")
    )

    return bytes(header)


def deterministic_tar_bytes(root: Path) -> bytes:
    """
    Canonical archive payload:
      seymour-runtime/
      seymour-runtime/<allow-listed runtime tree>

    uid/gid=0, mtime=0, stable lexical ordering.
    """

    output = io.BytesIO()

    root_name = "seymour-runtime"

    entries = [root] + sorted(
        root.rglob("*"),
        key=lambda item: item.relative_to(root).as_posix(),
    )

    for path in entries:
        if path == root:
            relative = ""
        else:
            relative = path.relative_to(root).as_posix()

        archive_name = (
            root_name
            if not relative
            else f"{root_name}/{relative}"
        )

        if path.is_dir():
            archive_name += "/"

            output.write(
                _tar_header(
                    name=archive_name,
                    mode=stat.S_IMODE(path.stat().st_mode),
                    size=0,
                    typeflag=b"5",
                )
            )

            continue

        if not path.is_file():
            raise RuntimeError(
                f"Unsupported runtime artifact type: {relative}"
            )

        data = path.read_bytes()

        output.write(
            _tar_header(
                name=archive_name,
                mode=stat.S_IMODE(path.stat().st_mode),
                size=len(data),
                typeflag=b"0",
            )
        )

        output.write(data)

        padding = (-len(data)) % 512

        if padding:
            output.write(b"\0" * padding)

    output.write(b"\0" * 1024)

    return output.getvalue()


def write_archive(root: Path) -> None:
    tar_payload = deterministic_tar_bytes(root)

    with ARCHIVE.open("wb") as raw:
        with gzip.GzipFile(
            filename="",
            mode="wb",
            fileobj=raw,
            mtime=0,
        ) as zipped:
            zipped.write(tar_payload)


def main() -> int:
    if BUILD.exists():
        shutil.rmtree(BUILD)

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

    clean_generated_junk()

    payload_sha, payload_entries = (
        installer_payload_manifest(OUTPUT)
    )

    revision = source_revision()

    write_archive(OUTPUT)

    archive_sha = file_sha256(ARCHIVE)

    metadata = {
        "schemaVersion": 1,
        "artifactType": "seymour-blockchain-target-runtime",
        "runtimeVersion": RUNTIME_VERSION,
        "sourceRevision": revision,
        "archiveFile": ARCHIVE.name,
        "archiveSha256": archive_sha,
        "payloadManifestSha256": payload_sha,
        "payloadFileCount": len(payload_entries),
        "archiveFormat": "tar.gz",
    }

    METADATA.write_text(
        json.dumps(
            metadata,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print(OUTPUT)
    print(ARCHIVE)
    print(METADATA)
    print(
        "archiveSha256="
        + archive_sha
    )
    print(
        "payloadManifestSha256="
        + payload_sha
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
