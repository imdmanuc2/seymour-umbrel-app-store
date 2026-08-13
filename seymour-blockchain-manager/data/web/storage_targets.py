from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from shared.blockchain_install import (
    StorageTarget,
    StorageTargetType,
    discover,
    registered_remote_target,
)

UMB_REL_DATA_DIRECTORY = Path(
    os.environ.get("SEYMOUR_UMBREL_DATA_DIRECTORY", "/home/umbrel/umbrel")
)
REMOTE_TARGETS_PATH = Path(
    os.environ.get("SEYMOUR_STORAGE_TARGETS_PATH", "/evidence/storage-targets.json")
)

def _local_path() -> Path:
    configured = os.environ.get(
        "SEYMOUR_INSTALL_LOCAL_STORAGE_PATH",
        "",
    ).strip()

    if configured:
        candidate = Path(configured)
        if candidate.exists():
            return candidate

    if UMB_REL_DATA_DIRECTORY.exists():
        return UMB_REL_DATA_DIRECTORY

    return Path("/")

def _registered_remote_targets() -> list[StorageTarget]:
    if not REMOTE_TARGETS_PATH.is_file():
        return []
    try:
        payload = json.loads(REMOTE_TARGETS_PATH.read_text())
    except Exception:
        return []
    items = payload if isinstance(payload, list) else payload.get("targets", [])
    results = []
    for item in items:
        if not isinstance(item, dict):
            continue
        mount_path = Path(str(item.get("mountPath", "")).strip())
        remote_host = str(item.get("remoteHost", "")).strip()
        source = str(item.get("source", "")).strip()
        if not str(mount_path) or not remote_host or not source:
            continue
        try:
            results.append(
                registered_remote_target(
                    mount_path=mount_path,
                    remote_host=remote_host,
                    source=source,
                    filesystem=str(item.get("filesystem", "nfs")),
                    persistent=bool(item.get("persistent", True)),
                    check_writable=False,
                )
            )
        except Exception:
            continue
    return results

def storage_targets() -> dict[str, Any]:
    found = discover(local_path=_local_path(), check_writable=False)
    by_id = {target.target_id: target for target in found}
    for target in _registered_remote_targets():
        by_id[target.target_id] = target
    targets = sorted(
        by_id.values(),
        key=lambda target: (
            0 if target.target_type == StorageTargetType.LOCAL else
            1 if target.target_type == StorageTargetType.ATTACHED else 2,
            -target.free_bytes,
            target.path,
        ),
    )
    return {
        "contract": "seymour.blockchain-storage-targets",
        "version": "1.0",
        "targetCount": len(targets),
        "targets": [target.to_dict() for target in targets],
    }

def target_by_id(target_id: str) -> StorageTarget | None:
    wanted = str(target_id).strip()
    for item in storage_targets()["targets"]:
        if item["target_id"] != wanted:
            continue
        return StorageTarget(
            target_id=item["target_id"],
            target_type=StorageTargetType(item["type"]),
            host=item["host"],
            path=item["path"],
            filesystem=item["filesystem"],
            source=item.get("source"),
            total_bytes=int(item["total_bytes"]),
            used_bytes=int(item["used_bytes"]),
            free_bytes=int(item["free_bytes"]),
            writable=bool(item["writable"]),
            persistent=bool(item["persistent"]),
            reachable=bool(item["reachable"]),
            mount_point=item.get("mount_point"),
            remote_host=item.get("remote_host"),
        )
    return None
