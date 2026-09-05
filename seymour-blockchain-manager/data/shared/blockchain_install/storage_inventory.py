from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .models import StorageTarget, StorageTargetType
from .storage import (
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
