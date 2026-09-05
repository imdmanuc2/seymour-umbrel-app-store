from __future__ import annotations
import hashlib, os, shutil, socket, tempfile
from pathlib import Path
from .models import StorageTarget, StorageTargetType

NETWORK_FILESYSTEMS = {"nfs","nfs4","cifs","smb3","sshfs","fuse.sshfs"}
PSEUDO_FILESYSTEMS = {
    "proc",
    "sysfs",
    "tmpfs",
    "devtmpfs",
    "devpts",
    "cgroup",
    "cgroup2",
    "overlay",
    "squashfs",
    "tracefs",
    "securityfs",
    "pstore",
    "debugfs",
    "mqueue",
    "hugetlbfs",
    "fusectl",
    "configfs",
    "ramfs",
    "autofs",
    "bpf",
    "binfmt_misc",
    "fuse.gvfsd-fuse",
}

def _target_id(kind: str, host: str, path: str) -> str:
    h = hashlib.sha256(f"{kind}|{host}|{path}".encode()).hexdigest()[:12]
    return f"{kind}-{h}"

def _decode(value: str) -> str:
    return value.replace("\\040"," ").replace("\\011","\t").replace("\\012","\n").replace("\\134","\\")

def read_mounts(path: Path = Path("/proc/mounts")) -> list[dict[str,str]]:
    try:
        lines = path.read_text().splitlines()
    except Exception:
        return []
    out = []
    for line in lines:
        parts = line.split()
        if len(parts) >= 4:
            out.append({
                "source": _decode(parts[0]),
                "mountPoint": _decode(parts[1]),
                "filesystem": parts[2],
                "options": parts[3],
            })
    return out

def probe_writable(path: Path) -> bool:
    if not path.is_dir():
        return False
    try:
        with tempfile.NamedTemporaryFile(prefix=".seymour-write-test-", dir=path, delete=True) as f:
            f.write(b"seymour")
            f.flush()
            os.fsync(f.fileno())
        return True
    except Exception:
        return False


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

def target_from_path(
    path: Path,
    *,
    target_type: StorageTargetType,
    filesystem: str = "unknown",
    source: str | None = None,
    host: str | None = None,
    persistent: bool = True,
    reachable: bool = True,
    remote_host: str | None = None,
    check_writable: bool = True,
) -> StorageTarget:
    resolved = path.resolve()
    usage = shutil.disk_usage(resolved)
    hostname = host or socket.gethostname()
    return StorageTarget(
        target_id=_target_id(target_type.value, hostname, str(resolved)),
        target_type=target_type,
        host=hostname,
        path=str(resolved),
        filesystem=filesystem,
        source=source,
        total_bytes=usage.total,
        used_bytes=usage.used,
        free_bytes=usage.free,
        writable=probe_writable(resolved) if check_writable else os.access(resolved, os.W_OK),
        persistent=persistent,
        reachable=reachable,
        mount_point=str(resolved),
        remote_host=remote_host,
        filesystem_uuid=filesystem_uuid_for_source(source),
    )

def discover(
    *,
    local_path: Path,
    mounts_path: Path = Path("/proc/mounts"),
    check_writable: bool = False,
) -> list[StorageTarget]:
    local = local_path.resolve()
    host = socket.gethostname()
    mounts = read_mounts(mounts_path)
    results = []
    seen = set()

    local_mount = None
    for m in mounts:
        mp = Path(m["mountPoint"])
        try:
            local.relative_to(mp)
        except Exception:
            continue
        if local_mount is None or len(str(mp)) > len(local_mount["mountPoint"]):
            local_mount = m

    lt = target_from_path(
        local,
        target_type=StorageTargetType.LOCAL,
        filesystem=local_mount["filesystem"] if local_mount else "unknown",
        source=local_mount["source"] if local_mount else None,
        host=host,
        check_writable=check_writable,
    )
    results.append(lt)
    seen.add(lt.path)

    for m in mounts:
        if m["filesystem"] in PSEUDO_FILESYSTEMS:
            continue
        mp = Path(m["mountPoint"])

        try:
            if not mp.is_dir():
                continue
            resolved = str(mp.resolve())
        except (PermissionError, OSError):
            continue
        if resolved in seen:
            continue
        is_remote = m["filesystem"] in NETWORK_FILESYSTEMS or ":" in m["source"]
        kind = StorageTargetType.REMOTE if is_remote else StorageTargetType.ATTACHED
        remote_host = m["source"].split(":",1)[0] if is_remote and ":" in m["source"] else None
        try:
            t = target_from_path(
                mp,
                target_type=kind,
                filesystem=m["filesystem"],
                source=m["source"],
                host=host,
                persistent=("noauto" not in m["options"]),
                reachable=True,
                remote_host=remote_host,
                check_writable=check_writable,
            )
        except Exception:
            continue
        results.append(t)
        seen.add(t.path)

    return results

def registered_remote_target(
    *,
    mount_path: Path,
    remote_host: str,
    source: str,
    filesystem: str = "nfs",
    persistent: bool = True,
    check_writable: bool = True,
) -> StorageTarget:
    if not mount_path.is_dir():
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
