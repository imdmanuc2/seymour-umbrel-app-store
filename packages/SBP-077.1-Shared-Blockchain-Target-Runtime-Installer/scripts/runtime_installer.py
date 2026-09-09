#!/usr/bin/env python3
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import shutil
import stat
import tempfile
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable


CONTRACT = "seymour.blockchain-target-runtime.installation"
CONTRACT_VERSION = 1
DEFAULT_UMBREL_ROOT = Path("/home/umbrel/umbrel")

REQUIRED_FILES = (
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

EXECUTABLE_FILES = (
    "scripts/seymour-blockchain-install",
    "scripts/seymour-install-btc",
    "scripts/seymour-install-bch",
    "scripts/seymour-install-monero",
    "scripts/seymour-umbrel-app",
    "scripts/seymour-umbrel-runtime",
)

FORBIDDEN_TOP_LEVEL = (
    "seymour-blockchain-manager",
    "nexus-command-center",
    "packages",
    "tests",
    ".git",
)


class RuntimeInstallError(RuntimeError):
    pass


@dataclass(frozen=True)
class RuntimePaths:
    umbrel_root: Path

    @property
    def current(self) -> Path:
        return self.umbrel_root / "seymour-runtime"

    @property
    def previous(self) -> Path:
        return self.umbrel_root / "seymour-runtime.previous"

    @property
    def evidence_root(self) -> Path:
        return (
            self.umbrel_root
            / "seymour-evidence"
            / "blockchain-target-runtime"
        )

    @property
    def history(self) -> Path:
        return self.evidence_root / "history"

    @property
    def lock(self) -> Path:
        return self.evidence_root / "deployment.lock"

    @property
    def current_evidence(self) -> Path:
        return self.evidence_root / "current.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fsync_directory(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )

    temporary = Path(temporary_name)

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(
                payload,
                handle,
                indent=2,
                sort_keys=True,
            )
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())

        os.replace(temporary, path)
        _fsync_directory(path.parent)
    finally:
        if temporary.exists():
            temporary.unlink()


def verify_runtime(root: Path) -> None:
    root = root.resolve()

    if not root.is_dir():
        raise RuntimeInstallError(
            "runtime artifact is not a directory"
        )

    for relative in REQUIRED_FILES:
        path = root / relative
        if not path.is_file():
            raise RuntimeInstallError(
                f"runtime artifact missing required file: {relative}"
            )

    for forbidden in FORBIDDEN_TOP_LEVEL:
        if (root / forbidden).exists():
            raise RuntimeInstallError(
                f"runtime artifact contains forbidden path: {forbidden}"
            )

    for relative in EXECUTABLE_FILES:
        path = root / relative
        if not (path.stat().st_mode & stat.S_IXUSR):
            raise RuntimeInstallError(
                f"runtime executable is not executable: {relative}"
            )

    try:
        catalog = json.loads(
            (
                root
                / "shared/provider_catalog/providers.v1.json"
            ).read_text(encoding="utf-8")
        )
    except Exception as exc:
        raise RuntimeInstallError(
            f"provider catalog cannot be read: {exc}"
        ) from exc

    if not isinstance(catalog, dict):
        raise RuntimeInstallError(
            "provider catalog is invalid"
        )


def payload_manifest(root: Path) -> tuple[str, list[dict]]:
    entries: list[dict] = []

    for path in sorted(
        (item for item in root.rglob("*") if item.is_file()),
        key=lambda item: item.relative_to(root).as_posix(),
    ):
        relative = path.relative_to(root).as_posix()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        mode = stat.S_IMODE(path.stat().st_mode)

        entries.append(
            {
                "path": relative,
                "sha256": digest,
                "mode": f"{mode:04o}",
            }
        )

    encoded = json.dumps(
        entries,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest(), entries


def copy_runtime(source: Path, destination: Path) -> None:
    shutil.copytree(
        source,
        destination,
        copy_function=shutil.copy2,
        symlinks=False,
    )


class RuntimeInstaller:
    def __init__(
        self,
        umbrel_root: Path = DEFAULT_UMBREL_ROOT,
        verifier: Callable[[Path], None] = verify_runtime,
    ):
        if not umbrel_root.is_absolute():
            raise ValueError("Umbrel root must be absolute")

        self.paths = RuntimePaths(umbrel_root)
        self.verifier = verifier

    def _prepare(self) -> None:
        self.paths.umbrel_root.mkdir(
            parents=True,
            exist_ok=True,
        )
        self.paths.history.mkdir(
            parents=True,
            exist_ok=True,
        )

    def _lock_handle(self):
        self._prepare()

        handle = self.paths.lock.open("a+")

        try:
            fcntl.flock(
                handle.fileno(),
                fcntl.LOCK_EX | fcntl.LOCK_NB,
            )
        except BlockingIOError as exc:
            handle.close()
            raise RuntimeInstallError(
                "runtime deployment is already in progress"
            ) from exc

        return handle

    def _evidence(
        self,
        *,
        operation_id: str,
        operation: str,
        runtime_version: str,
        source_revision: str,
        manifest_sha256: str,
        status: str,
        error: str | None = None,
    ) -> dict:
        payload = {
            "contract": CONTRACT,
            "version": CONTRACT_VERSION,
            "operationId": operation_id,
            "operation": operation,
            "runtimeVersion": runtime_version,
            "sourceRevision": source_revision,
            "payloadManifestSha256": manifest_sha256,
            "installedAt": utc_now(),
            "status": status,
            "previousRuntimeAvailable": self.paths.previous.is_dir(),
        }

        if error:
            payload["error"] = error

        return payload

    def _write_history(self, payload: dict) -> None:
        operation_id = payload["operationId"]

        atomic_json(
            self.paths.history / f"{operation_id}.json",
            payload,
        )

    def _write_current(self, payload: dict) -> None:
        atomic_json(
            self.paths.current_evidence,
            payload,
        )

    def _write_success_evidence(self, payload: dict) -> None:
        self._write_history(payload)
        self._write_current(payload)

    def install(
        self,
        *,
        artifact: Path,
        runtime_version: str,
        source_revision: str,
        expected_manifest_sha256: str,
    ) -> dict:
        artifact = artifact.resolve()

        if not runtime_version.strip():
            raise RuntimeInstallError(
                "runtime version is required"
            )

        if not source_revision.strip():
            raise RuntimeInstallError(
                "source revision is required"
            )

        expected_manifest_sha256 = (
            expected_manifest_sha256.strip().lower()
        )

        if (
            len(expected_manifest_sha256) != 64
            or any(
                character not in "0123456789abcdef"
                for character in expected_manifest_sha256
            )
        ):
            raise RuntimeInstallError(
                "expected payload manifest SHA-256 is invalid"
            )

        operation_id = str(uuid.uuid4())
        lock_handle = self._lock_handle()

        stage: Path | None = None
        old_moved = False
        promoted = False
        manifest_sha256 = ""

        try:
            self.verifier(artifact)
            manifest_sha256, _ = payload_manifest(artifact)

            if manifest_sha256 != expected_manifest_sha256:
                raise RuntimeInstallError(
                    "runtime artifact manifest does not match "
                    "reviewed payload manifest"
                )

            stage = Path(
                tempfile.mkdtemp(
                    prefix=".seymour-runtime.stage.",
                    dir=str(self.paths.umbrel_root),
                )
            )

            stage.rmdir()
            copy_runtime(artifact, stage)

            self.verifier(stage)

            staged_manifest, _ = payload_manifest(stage)
            if staged_manifest != manifest_sha256:
                raise RuntimeInstallError(
                    "staged runtime manifest does not match source artifact"
                )

            if self.paths.previous.exists():
                shutil.rmtree(self.paths.previous)
                _fsync_directory(
                    self.paths.umbrel_root
                )

            if self.paths.current.exists():
                os.replace(
                    self.paths.current,
                    self.paths.previous,
                )
                old_moved = True

            os.replace(stage, self.paths.current)
            stage = None
            promoted = True
            _fsync_directory(self.paths.umbrel_root)

            self.verifier(self.paths.current)

            promoted_manifest, _ = payload_manifest(
                self.paths.current
            )
            if promoted_manifest != manifest_sha256:
                raise RuntimeInstallError(
                    "promoted runtime manifest does not match artifact"
                )

            payload = self._evidence(
                operation_id=operation_id,
                operation="install",
                runtime_version=runtime_version.strip(),
                source_revision=source_revision.strip(),
                manifest_sha256=manifest_sha256,
                status="installed",
            )
            self._write_success_evidence(payload)
            return payload

        except Exception as exc:
            rollback_error = None

            try:
                if promoted and self.paths.current.exists():
                    shutil.rmtree(self.paths.current)
                    _fsync_directory(
                        self.paths.umbrel_root
                    )

                if old_moved and self.paths.previous.exists():
                    os.replace(
                        self.paths.previous,
                        self.paths.current,
                    )
                    _fsync_directory(
                        self.paths.umbrel_root
                    )
            except Exception as rollback_exc:
                rollback_error = str(rollback_exc)

            error = str(exc)
            if rollback_error:
                error += (
                    "; automatic rollback failed: "
                    + rollback_error
                )

            payload = self._evidence(
                operation_id=operation_id,
                operation="install",
                runtime_version=runtime_version.strip(),
                source_revision=source_revision.strip(),
                manifest_sha256=manifest_sha256,
                status="failed",
                error=error,
            )

            try:
                self._write_history(payload)
            except Exception:
                pass

            if isinstance(exc, RuntimeInstallError):
                raise RuntimeInstallError(error) from exc

            raise RuntimeInstallError(error) from exc

        finally:
            if stage is not None and stage.exists():
                shutil.rmtree(stage)

            fcntl.flock(
                lock_handle.fileno(),
                fcntl.LOCK_UN,
            )
            lock_handle.close()

    def rollback(self) -> dict:
        operation_id = str(uuid.uuid4())
        lock_handle = self._lock_handle()
        manifest_sha256 = ""

        try:
            if not self.paths.previous.is_dir():
                raise RuntimeInstallError(
                    "no previous runtime is available"
                )

            self.verifier(self.paths.previous)
            manifest_sha256, _ = payload_manifest(
                self.paths.previous
            )

            displaced = Path(
                tempfile.mkdtemp(
                    prefix=".seymour-runtime.displaced.",
                    dir=str(self.paths.umbrel_root),
                )
            )
            displaced.rmdir()

            try:
                if self.paths.current.exists():
                    os.replace(
                        self.paths.current,
                        displaced,
                    )

                os.replace(
                    self.paths.previous,
                    self.paths.current,
                )
                _fsync_directory(self.paths.umbrel_root)

                self.verifier(self.paths.current)

                current_manifest, _ = payload_manifest(
                    self.paths.current
                )
                if current_manifest != manifest_sha256:
                    raise RuntimeInstallError(
                        "rolled-back runtime manifest mismatch"
                    )

                if displaced.exists():
                    os.replace(
                        displaced,
                        self.paths.previous,
                    )
                    _fsync_directory(
                        self.paths.umbrel_root
                    )

            except Exception:
                recovery_error = None

                try:
                    if self.paths.current.exists():
                        shutil.rmtree(
                            self.paths.current
                        )
                        _fsync_directory(
                            self.paths.umbrel_root
                        )

                    if displaced.exists():
                        os.replace(
                            displaced,
                            self.paths.current,
                        )
                        _fsync_directory(
                            self.paths.umbrel_root
                        )
                except Exception as exc:
                    recovery_error = str(exc)

                if recovery_error:
                    raise RuntimeInstallError(
                        "rollback failed and original runtime "
                        "could not be restored: "
                        + recovery_error
                    )

                raise

            payload = self._evidence(
                operation_id=operation_id,
                operation="rollback",
                runtime_version="previous",
                source_revision="previous",
                manifest_sha256=manifest_sha256,
                status="rolled-back",
            )
            self._write_success_evidence(payload)
            return payload

        except Exception as exc:
            error = str(exc)

            payload = self._evidence(
                operation_id=operation_id,
                operation="rollback",
                runtime_version="previous",
                source_revision="previous",
                manifest_sha256=manifest_sha256,
                status="failed",
                error=error,
            )

            try:
                self._write_history(payload)
            except Exception:
                pass

            if isinstance(exc, RuntimeInstallError):
                raise RuntimeInstallError(error) from exc

            raise RuntimeInstallError(error) from exc

        finally:
            fcntl.flock(
                lock_handle.fileno(),
                fcntl.LOCK_UN,
            )
            lock_handle.close()
