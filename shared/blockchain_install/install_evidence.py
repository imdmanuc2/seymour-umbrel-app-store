from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any

from .execution import InstallResult
from .request import InstallRequest


CONTRACT = "seymour.blockchain-installation"
CONTRACT_VERSION = 1

_PROVIDER_ID_RE = re.compile(
    r"^[a-z0-9][a-z0-9-]{0,63}$"
)

_STORAGE_TARGET_ID_RE = re.compile(
    r"^[A-Za-z0-9_.:-]{1,128}$"
)

_OPERATION_ID_RE = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$"
)


def utc_now() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


def _required(
    value: Any,
    *,
    name: str,
    pattern: re.Pattern[str],
) -> str:
    normalized = str(
        value or ""
    ).strip()

    if not pattern.fullmatch(
        normalized
    ):
        raise ValueError(
            f"Invalid {name}"
        )

    return normalized


def _fsync_directory(
    path: Path,
) -> None:
    fd = os.open(
        path,
        os.O_RDONLY,
    )

    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_json(
    path: Path,
    payload: dict[str, Any],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )

    temporary = Path(
        temporary_name
    )

    try:
        with os.fdopen(
            fd,
            "w",
            encoding="utf-8",
        ) as handle:
            json.dump(
                payload,
                handle,
                indent=2,
                sort_keys=True,
            )
            handle.write("\n")
            handle.flush()
            os.fsync(
                handle.fileno()
            )

        os.replace(
            temporary,
            path,
        )

        _fsync_directory(
            path.parent
        )

    finally:
        if temporary.exists():
            temporary.unlink()


@dataclass(
    frozen=True,
    slots=True,
)
class ProviderInstallEvidencePaths:
    umbrel_root: Path

    def __post_init__(self) -> None:
        root = Path(
            self.umbrel_root
        )

        if not root.is_absolute():
            raise ValueError(
                "Umbrel data directory must be absolute"
            )

        object.__setattr__(
            self,
            "umbrel_root",
            root,
        )

    @property
    def evidence_root(self) -> Path:
        return (
            self.umbrel_root
            / "seymour-evidence"
            / "blockchain-install"
            / "installations"
        )

    @property
    def history(self) -> Path:
        return (
            self.evidence_root
            / "history"
        )

    @property
    def current(self) -> Path:
        return (
            self.evidence_root
            / "current"
        )

    def history_path(
        self,
        operation_id: str,
    ) -> Path:
        operation_id = _required(
            operation_id,
            name="operation_id",
            pattern=_OPERATION_ID_RE,
        )

        return (
            self.history
            / f"{operation_id}.json"
        )

    def current_path(
        self,
        provider_id: str,
    ) -> Path:
        provider_id = _required(
            provider_id,
            name="provider_id",
            pattern=_PROVIDER_ID_RE,
        )

        return (
            self.current
            / f"{provider_id}.json"
        )


class ProviderInstallEvidenceWriter:
    def __init__(
        self,
        *,
        umbrel_root: Path,
    ) -> None:
        self.paths = (
            ProviderInstallEvidencePaths(
                Path(umbrel_root)
            )
        )

    @staticmethod
    def _payload(
        *,
        request: InstallRequest,
        result: InstallResult,
    ) -> dict[str, Any]:
        provider_id = _required(
            request.provider_id,
            name="provider_id",
            pattern=_PROVIDER_ID_RE,
        )

        storage_target_id = _required(
            request.storage_target_id,
            name="storage_target_id",
            pattern=_STORAGE_TARGET_ID_RE,
        )

        operation_id = _required(
            result.operation_id,
            name="operation_id",
            pattern=_OPERATION_ID_RE,
        )

        verification = (
            result.verification
            if isinstance(
                result.verification,
                dict,
            )
            else {}
        )

        verified = (
            verification.get(
                "verified"
            )
            is True
        )

        evidence = (
            verification.get(
                "evidence"
            )
            if isinstance(
                verification.get(
                    "evidence"
                ),
                dict,
            )
            else {}
        )

        verified_storage = str(
            evidence.get(
                "storageTargetId"
            )
            or ""
        ).strip()

        if (
            verified
            and verified_storage
            != storage_target_id
        ):
            raise ValueError(
                "Verified storage target identity mismatch"
            )

        state_verified = bool(
            (
                evidence.get("state")
                or {}
            ).get("success")
        )

        data_mount_matches = (
            evidence.get(
                "runtimeDataMountMatches"
            )
            is True
        )

        blocks_mount_matches = (
            evidence.get(
                "runtimeBlocksMountMatches"
            )
            is True
        )

        succeeded = (
            result.status
            == "succeeded"
            and result.succeeded
            and verified
            and state_verified
            and data_mount_matches
            and blocks_mount_matches
        )

        status = (
            "installed"
            if succeeded
            else "failed"
        )

        payload: dict[str, Any] = {
            "contract": CONTRACT,
            "version": (
                CONTRACT_VERSION
            ),
            "operationId": (
                operation_id
            ),
            "operation": "install",
            "providerId": (
                provider_id
            ),
            "storageTargetId": (
                storage_target_id
            ),
            "status": status,
            "verified": (
                succeeded
            ),
            "stateVerified": (
                state_verified
            ),
            "runtimeDataMountMatches": (
                data_mount_matches
            ),
            "runtimeBlocksMountMatches": (
                blocks_mount_matches
            ),
            "bindingMode": str(
                evidence.get(
                    "bindingMode"
                )
                or ""
            ),
            "recordedAt": utc_now(),
        }

        if not succeeded:
            error = str(
                result.error
                or verification.get(
                    "error"
                )
                or (
                    "Provider installation "
                    "verification failed"
                )
            ).strip()

            payload["error"] = error

        return payload

    def write(
        self,
        *,
        request: InstallRequest,
        result: InstallResult,
    ) -> dict[str, Any]:
        payload = self._payload(
            request=request,
            result=result,
        )

        history_path = (
            self.paths.history_path(
                payload[
                    "operationId"
                ]
            )
        )

        atomic_json(
            history_path,
            payload,
        )

        if (
            payload["status"]
            == "installed"
            and payload["verified"]
            is True
        ):
            atomic_json(
                self.paths.current_path(
                    payload[
                        "providerId"
                    ]
                ),
                payload,
            )

        return payload
