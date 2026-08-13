#!/usr/bin/env python3
from pathlib import Path
import sys

repo = Path(sys.argv[1]).resolve()

# models.py: persist optional filesystem UUID identity.
models = repo / "shared/blockchain_install/models.py"
text = models.read_text()
anchor = "    remote_host: str | None = None\n    def to_dict(self) -> dict[str, Any]:\n"
replacement = "    remote_host: str | None = None\n    filesystem_uuid: str | None = None\n    def to_dict(self) -> dict[str, Any]:\n"
if anchor in text:
    text = text.replace(anchor, replacement, 1)
elif "filesystem_uuid: str | None = None" not in text:
    raise SystemExit("SBP-060.3 models anchor not found")
models.write_text(text)

# storage.py: derive UUID and add fail-closed live mount verification.
storage = repo / "shared/blockchain_install/storage.py"
text = storage.read_text()
if "def filesystem_uuid_for_source(" not in text:
    pos = text.find("\ndef target_from_path(")
    if pos < 0:
        raise SystemExit("SBP-060.3 target_from_path anchor not found")
    helper = r'''

def filesystem_uuid_for_source(source: str | None) -> str | None:
    if not source or not str(source).startswith("/dev/"):
        return None
    try:
        wanted = Path(source).resolve()
        by_uuid = Path("/dev/disk/by-uuid")
        if not by_uuid.is_dir():
            return None
        for entry in by_uuid.iterdir():
            try:
                if entry.resolve() == wanted:
                    return entry.name
            except OSError:
                continue
    except OSError:
        return None
    return None


def _mount_for_path(path: Path, mounts: list[dict[str, str]] | None = None) -> dict[str, str] | None:
    resolved = path.resolve()
    best = None
    for mount in mounts if mounts is not None else read_mounts():
        mp = Path(mount["mountPoint"])
        try:
            resolved.relative_to(mp.resolve())
        except (ValueError, OSError):
            continue
        if best is None or len(str(mp)) > len(best["mountPoint"]):
            best = mount
    return best


def verify_storage_target(
    storage_target: StorageTarget,
    *,
    minimum_free_bytes: int = 0,
    data_path: Path | None = None,
) -> dict[str, object]:
    target_path = Path(storage_target.path)
    result: dict[str, object] = {
        "targetId": storage_target.target_id,
        "path": str(target_path),
        "type": storage_target.target_type.value,
        "exists": False,
        "isMountPoint": False,
        "mountPoint": None,
        "source": None,
        "filesystem": None,
        "filesystemUuid": None,
        "expectedSource": storage_target.source,
        "expectedFilesystem": storage_target.filesystem,
        "expectedFilesystemUuid": storage_target.filesystem_uuid,
        "sourceMatches": False,
        "filesystemMatches": False,
        "filesystemUuidMatches": False,
        "writable": False,
        "freeBytes": 0,
        "capacityHealthy": False,
        "dataPathContained": True,
        "healthy": False,
        "errors": [],
    }
    errors = result["errors"]

    if not target_path.is_dir():
        errors.append("Selected storage target path does not exist.")
        return result

    result["exists"] = True
    mount = _mount_for_path(target_path)
    if mount is None:
        errors.append("Selected storage target is not backed by a mounted filesystem.")
        return result

    mount_point = Path(mount["mountPoint"])
    result["mountPoint"] = str(mount_point)
    result["source"] = mount["source"]
    result["filesystem"] = mount["filesystem"]
    result["isMountPoint"] = target_path.resolve() == mount_point.resolve()

    if storage_target.target_type != StorageTargetType.LOCAL and not result["isMountPoint"]:
        errors.append("Selected attached/remote storage target is no longer mounted at its configured path.")

    expected_fs = (storage_target.filesystem or "").strip()
    result["filesystemMatches"] = (
        not expected_fs or expected_fs == "unknown" or mount["filesystem"] == expected_fs
    )
    if not result["filesystemMatches"]:
        errors.append("Mounted filesystem type does not match the selected storage target.")

    expected_source = (storage_target.source or "").strip()
    result["sourceMatches"] = not expected_source or mount["source"] == expected_source

    actual_uuid = filesystem_uuid_for_source(mount["source"])
    result["filesystemUuid"] = actual_uuid
    expected_uuid = storage_target.filesystem_uuid
    result["filesystemUuidMatches"] = not expected_uuid or actual_uuid == expected_uuid

    if expected_uuid and not result["filesystemUuidMatches"]:
        errors.append("Mounted filesystem UUID does not match the selected storage target.")
    elif expected_source and not result["sourceMatches"]:
        errors.append("Mounted storage source does not match the selected storage target.")

    try:
        usage = shutil.disk_usage(target_path)
        result["freeBytes"] = usage.free
        result["capacityHealthy"] = usage.free >= int(minimum_free_bytes)
    except Exception as exc:
        errors.append(f"Unable to read selected storage capacity: {exc}")

    result["writable"] = probe_writable(target_path)
    if not result["writable"]:
        errors.append("Selected storage target is not writable.")
    if not result["capacityHealthy"]:
        errors.append("Selected storage target does not have enough free capacity.")

    if data_path is not None:
        try:
            Path(data_path).resolve().relative_to(target_path.resolve())
        except (ValueError, OSError):
            result["dataPathContained"] = False
            errors.append("Blockchain data path escapes the selected storage target.")

    result["healthy"] = not errors
    return result
'''
    text = text[:pos] + helper + text[pos:]

old = "        remote_host=remote_host,\n    )\n"
new = "        remote_host=remote_host,\n        filesystem_uuid=filesystem_uuid_for_source(source),\n    )\n"
if old in text:
    text = text.replace(old, new, 1)
elif "filesystem_uuid=filesystem_uuid_for_source(source)" not in text:
    raise SystemExit("SBP-060.3 target identity anchor not found")

old = '''    if not mount_path.is_dir():
        raise ValueError(f"Remote storage mount is unavailable: {mount_path}")
    return target_from_path(
        mount_path,
        target_type=StorageTargetType.REMOTE,
        filesystem=filesystem,
        source=source,
        remote_host=remote_host,
        persistent=persistent,
        reachable=True,
        check_writable=check_writable,
    )
'''
new = '''    if not mount_path.is_dir():
        raise ValueError(f"Remote storage mount is unavailable: {mount_path}")
    live = _mount_for_path(mount_path, read_mounts())
    if live is None or Path(live["mountPoint"]).resolve() != mount_path.resolve():
        raise ValueError(f"Remote storage path is not mounted: {mount_path}")
    if filesystem and filesystem != "unknown" and live["filesystem"] != filesystem:
        raise ValueError(f"Remote storage filesystem mismatch: expected {filesystem}, got {live['filesystem']}")
    if source and live["source"] != source:
        raise ValueError(f"Remote storage source mismatch: expected {source}, got {live['source']}")
    return target_from_path(
        mount_path,
        target_type=StorageTargetType.REMOTE,
        filesystem=live["filesystem"],
        source=live["source"],
        remote_host=remote_host,
        persistent=persistent,
        reachable=True,
        check_writable=check_writable,
    )
'''
if old in text:
    text = text.replace(old, new, 1)
elif "Remote storage path is not mounted" not in text:
    raise SystemExit("SBP-060.3 remote registration anchor not found")
storage.write_text(text)

# __init__.py exports.
init = repo / "shared/blockchain_install/__init__.py"
text = init.read_text()
text = text.replace(
    "from .storage import discover, probe_writable, read_mounts, registered_remote_target, target_from_path",
    "from .storage import discover, filesystem_uuid_for_source, probe_writable, read_mounts, registered_remote_target, target_from_path, verify_storage_target",
    1,
)
if '"verify_storage_target"' not in text:
    text = text.replace(
        '"profile","read_mounts","registered_remote_target","target_from_path","umbrel_available",',
        '"profile","read_mounts","registered_remote_target","target_from_path","umbrel_available","filesystem_uuid_for_source","verify_storage_target",',
        1,
    )
init.write_text(text)

# preflight.py integrates live guard.
preflight = repo / "shared/blockchain_install/preflight.py"
text = preflight.read_text()
if "from .storage import verify_storage_target" not in text:
    text = text.replace(
        "from .models import CapacityPolicy, HostProfile, InstallPreflight, StorageTarget\n",
        "from .models import CapacityPolicy, HostProfile, InstallPreflight, StorageTarget\nfrom .storage import verify_storage_target\n",
        1,
    )
if "mount_guard = verify_storage_target(" not in text:
    text = text.replace(
        "    checks = {\n",
        "    mount_guard = verify_storage_target(storage_target, minimum_free_bytes=policy.required_bytes)\n    checks = {\n",
        1,
    )
    text = text.replace(
        '        "storageCapacityHealthy": storage_target.free_bytes >= policy.required_bytes,\n',
        '        "storageCapacityHealthy": storage_target.free_bytes >= policy.required_bytes,\n        "storageMountIdentityHealthy": bool(mount_guard["healthy"]),\n        "storageMountIdentity": mount_guard,\n',
        1,
    )
    text = text.replace(
        '    if not checks["storageCapacityHealthy"]: errors.append("Selected storage target does not have enough free capacity.")\n',
        '    if not checks["storageCapacityHealthy"]: errors.append("Selected storage target does not have enough free capacity.")\n    if not checks["storageMountIdentityHealthy"]: errors.extend(str(item) for item in mount_guard["errors"])\n',
        1,
    )
preflight.write_text(text)

# storage_targets.py preserves UUID.
targets = repo / "seymour-blockchain-manager/data/web/storage_targets.py"
text = targets.read_text()
anchor = "            remote_host=item.get(\"remote_host\"),\n        )\n"
replacement = "            remote_host=item.get(\"remote_host\"),\n            filesystem_uuid=item.get(\"filesystem_uuid\"),\n        )\n"
if anchor in text:
    text = text.replace(anchor, replacement, 1)
elif "filesystem_uuid=item.get" not in text:
    raise SystemExit("SBP-060.3 storage target reconstruction anchor not found")
targets.write_text(text)

# installer.py revalidates immediately before mkdir/execute.
installer = repo / "seymour-blockchain-manager/data/web/installer.py"
text = installer.read_text()
if "from shared.blockchain_install.storage import verify_storage_target" not in text:
    marker = "from storage_targets import storage_targets, target_by_id\n"
    if marker not in text:
        raise SystemExit("SBP-060.3 installer import anchor not found")
    text = text.replace(marker, marker + "from shared.blockchain_install.storage import verify_storage_target\n", 1)
anchor = "        data_path = Path(binding.data_path)\n        try:\n            data_path.mkdir(parents=True, exist_ok=True)\n"
replacement = '''        data_path = Path(binding.data_path)
        capacity = checks.get("capacity", {}) if isinstance(checks, dict) else {}
        required_bytes = int(capacity.get("required_bytes", 0)) if isinstance(capacity, dict) else 0
        storage_guard = verify_storage_target(
            selected_target,
            minimum_free_bytes=required_bytes,
            data_path=data_path,
        )
        operation.preflight["storageMountGuard"] = storage_guard
        if not storage_guard["healthy"]:
            operation.status = InstallStatus.FAILED
            operation.error = (
                "Selected blockchain storage failed live mount identity verification: "
                + "; ".join(str(item) for item in storage_guard["errors"])
            )
            operation.updated_at = utc_now()
            self._save(operation)
            return operation
        try:
            data_path.mkdir(parents=True, exist_ok=True)
'''
if anchor in text:
    text = text.replace(anchor, replacement, 1)
elif 'operation.preflight["storageMountGuard"]' not in text:
    raise SystemExit("SBP-060.3 installer mkdir anchor not found")
installer.write_text(text)

print("SBP-060.3 blockchain storage mount safety guard: PASS")
