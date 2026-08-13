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
