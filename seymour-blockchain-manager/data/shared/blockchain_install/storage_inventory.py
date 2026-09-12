from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import tempfile
from typing import Iterable

from .models import StorageTarget, StorageTargetType
from .storage import (
    _target_id,
    discover,
    registered_remote_target,
)


def registered_remote_targets(
    path: Path,
) -> list[StorageTarget]:
    source_path = Path(path)

    if not source_path.is_file():
        return []

    try:
        payload = json.loads(
            source_path.read_text()
        )
    except Exception:
        return []

    items = (
        payload
        if isinstance(payload, list)
        else payload.get("targets", [])
        if isinstance(payload, dict)
        else []
    )

    results: list[StorageTarget] = []

    for item in items:
        if not isinstance(item, dict):
            continue

        mount_text = str(
            item.get("mountPath", "")
        ).strip()
        remote_host = str(
            item.get("remoteHost", "")
        ).strip()
        source = str(
            item.get("source", "")
        ).strip()

        if (
            not mount_text
            or not remote_host
            or not source
        ):
            continue

        try:
            results.append(
                registered_remote_target(
                    mount_path=Path(mount_text),
                    remote_host=remote_host,
                    source=source,
                    filesystem=str(
                        item.get(
                            "filesystem",
                            "nfs",
                        )
                    ),
                    persistent=bool(
                        item.get(
                            "persistent",
                            True,
                        )
                    ),
                    check_writable=False,
                )
            )
        except Exception:
            continue

    return results


def _registered_target_payload(
    *,
    mount_path: Path,
    remote_host: str,
    source: str,
    filesystem: str = "nfs",
    persistent: bool = True,
    runtime_host: str | None = None,
) -> dict[str, object]:
    mount_text = str(Path(mount_path)).strip()
    host_text = str(remote_host).strip()
    source_text = str(source).strip()
    filesystem_text = str(filesystem).strip()

    if not mount_text or not Path(mount_text).is_absolute():
        raise ValueError(
            "Remote storage mount path must be absolute."
        )
    if not host_text:
        raise ValueError(
            "Remote storage host is required."
        )
    if not source_text:
        raise ValueError(
            "Remote storage source is required."
        )
    if not filesystem_text:
        raise ValueError(
            "Remote storage filesystem is required."
        )

    runtime_host_text = str(
        runtime_host or socket.gethostname()
    ).strip()

    if not runtime_host_text:
        raise ValueError(
            "Runtime host is required."
        )

    return {
        "targetId": _target_id(
            StorageTargetType.REMOTE.value,
            runtime_host_text,
            mount_text,
        ),
        "mountPath": mount_text,
        "remoteHost": host_text,
        "source": source_text,
        "filesystem": filesystem_text,
        "persistent": bool(persistent),
    }


def register_remote_target(
    path: Path,
    *,
    mount_path: Path,
    remote_host: str,
    source: str,
    filesystem: str = "nfs",
    persistent: bool = True,
    runtime_host: str | None = None,
) -> dict[str, object]:
    registry_path = Path(path)

    if not registry_path.is_absolute():
        raise ValueError(
            "Storage target registry path must be absolute."
        )

    item = _registered_target_payload(
        mount_path=mount_path,
        remote_host=remote_host,
        source=source,
        filesystem=filesystem,
        persistent=persistent,
        runtime_host=runtime_host,
    )

    existing: list[dict[str, object]] = []

    if registry_path.exists():
        try:
            payload = json.loads(
                registry_path.read_text()
            )
        except Exception as exc:
            raise ValueError(
                "Existing storage target registry is invalid."
            ) from exc

        values = (
            payload
            if isinstance(payload, list)
            else payload.get("targets", [])
            if isinstance(payload, dict)
            else None
        )

        if not isinstance(values, list):
            raise ValueError(
                "Existing storage target registry has invalid shape."
            )

        existing = [
            dict(value)
            for value in values
            if isinstance(value, dict)
        ]

    identity = str(
        item["targetId"]
    ).strip()

    retained = [
        value
        for value in existing
        if str(
            value.get("targetId", "")
        ).strip() != identity
    ]

    retained.append(item)

    retained.sort(
        key=lambda value: (
            str(value.get("targetId", "")),
            str(value.get("mountPath", "")),
        )
    )

    output = {
        "contract": "seymour.blockchain-storage-targets",
        "version": "1.0",
        "targets": retained,
    }

    registry_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    serialized = (
        json.dumps(
            output,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )

    temporary_path: Path | None = None

    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{registry_path.name}.",
            suffix=".tmp",
            dir=registry_path.parent,
            text=True,
        )
        temporary_path = Path(temporary_name)

        with os.fdopen(
            descriptor,
            "w",
            encoding="utf-8",
        ) as handle:
            handle.write(serialized)
            handle.flush()
            os.fsync(handle.fileno())

        os.replace(
            temporary_path,
            registry_path,
        )
        temporary_path = None

        directory_fd = os.open(
            registry_path.parent,
            os.O_RDONLY,
        )
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if (
            temporary_path is not None
            and temporary_path.exists()
        ):
            temporary_path.unlink()

    return output


def sort_storage_targets(
    targets: Iterable[StorageTarget],
) -> list[StorageTarget]:
    return sorted(
        targets,
        key=lambda target: (
            0
            if target.target_type
            == StorageTargetType.LOCAL
            else 1
            if target.target_type
            == StorageTargetType.ATTACHED
            else 2,
            -target.free_bytes,
            target.path,
        ),
    )


def storage_target_inventory(
    *,
    local_path: Path,
    remote_targets_path: Path | None = None,
) -> list[StorageTarget]:
    found = discover(
        local_path=Path(local_path),
        check_writable=False,
    )

    by_id = {
        target.target_id: target
        for target in found
    }

    if remote_targets_path is not None:
        for target in registered_remote_targets(
            Path(remote_targets_path)
        ):
            by_id[target.target_id] = target

    return sort_storage_targets(
        by_id.values()
    )


def storage_target_by_id(
    target_id: str,
    *,
    local_path: Path,
    remote_targets_path: Path | None = None,
) -> StorageTarget | None:
    wanted = str(target_id).strip()

    if not wanted:
        return None

    for target in storage_target_inventory(
        local_path=local_path,
        remote_targets_path=remote_targets_path,
    ):
        if target.target_id == wanted:
            return target

    return None
