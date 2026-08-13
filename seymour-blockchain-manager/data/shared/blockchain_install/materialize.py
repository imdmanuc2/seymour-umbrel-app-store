from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json
import os
import re
import shutil
import subprocess
from typing import Any

SAFE_HOST = re.compile(r"^[A-Za-z0-9._:-]+$")
SAFE_PATH = re.compile(r"^/[A-Za-z0-9._/:-]+$")


@dataclass(frozen=True)
class NfsMaterializationPlan:
    provider_id: str
    storage_host: str
    storage_path: str
    runtime_host: str
    runtime_mount_path: str
    nfs_source: str
    data_path: str
    exports_file: str
    fstab_file: str
    confirmation: str
    eligible: bool
    errors: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["errors"] = list(self.errors)
        return data


def _safe_host(value: str, label: str) -> str:
    text = str(value).strip()
    if not text or not SAFE_HOST.fullmatch(text):
        raise ValueError(f"Unsafe {label}: {value!r}")
    return text


def _safe_path(value: str | Path, label: str) -> Path:
    text = str(value).strip()
    if not text.startswith("/") or not SAFE_PATH.fullmatch(text):
        raise ValueError(f"Unsafe {label}: {value!r}")
    path = Path(text)
    if ".." in path.parts:
        raise ValueError(f"Unsafe {label}: parent traversal is not allowed")
    return path


def confirmation_token(provider_id: str, storage_host: str) -> str:
    provider = str(provider_id).strip()
    host = str(storage_host).strip()
    return f"MATERIALIZE-{provider}-ON-{host}"


def build_nfs_plan(
    *,
    provider_id: str,
    storage_host: str,
    storage_path: str | Path,
    runtime_host: str,
    runtime_mount_path: str | Path,
    client_cidr: str = "192.168.0.0/16",
    exports_file: str | Path = "/etc/exports.d/seymour-blockchain.exports",
    fstab_file: str | Path = "/etc/fstab",
) -> NfsMaterializationPlan:
    provider = _safe_host(provider_id, "provider ID")
    store_host = _safe_host(storage_host, "storage host")
    run_host = _safe_host(runtime_host, "runtime host")
    store_path = _safe_path(storage_path, "storage path")
    mount_path = _safe_path(runtime_mount_path, "runtime mount path")
    export_path = _safe_path(exports_file, "exports file")
    fstab_path = _safe_path(fstab_file, "fstab file")

    errors: list[str] = []
    if not client_cidr or "/" not in client_cidr:
        errors.append("Client CIDR is invalid.")

    source = f"{store_host}:{store_path}"
    data_path = str(mount_path / provider)

    return NfsMaterializationPlan(
        provider_id=provider,
        storage_host=store_host,
        storage_path=str(store_path),
        runtime_host=run_host,
        runtime_mount_path=str(mount_path),
        nfs_source=source,
        data_path=data_path,
        exports_file=str(export_path),
        fstab_file=str(fstab_path),
        confirmation=confirmation_token(provider, store_host),
        eligible=not errors,
        errors=tuple(errors),
    )


def command_available(name: str) -> bool:
    return shutil.which(name) is not None


def run(
    command: list[str],
    *,
    timeout: int = 30,
) -> dict[str, Any]:
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    return {
        "command": command,
        "returnCode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        "success": result.returncode == 0,
    }


def ensure_line(path: Path, line: str) -> bool:
    existing = path.read_text().splitlines() if path.exists() else []
    if line in existing:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        if existing:
            handle.write("\n")
        handle.write(line + "\n")
    return True


def verify_mount(
    *,
    mount_path: Path,
    minimum_free_bytes: int = 0,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": str(mount_path),
        "exists": mount_path.is_dir(),
        "mounted": os.path.ismount(mount_path),
        "writable": False,
        "freeBytes": 0,
        "healthy": False,
    }
    if not mount_path.is_dir():
        return result

    try:
        usage = shutil.disk_usage(mount_path)
        result["freeBytes"] = usage.free
    except Exception as exc:
        result["error"] = str(exc)
        return result

    probe = mount_path / ".seymour-materialization-write-test"
    try:
        probe.write_text("seymour\n")
        probe.unlink()
        result["writable"] = True
    except Exception as exc:
        result["writeError"] = str(exc)

    result["healthy"] = (
        result["mounted"]
        and result["writable"]
        and result["freeBytes"] >= int(minimum_free_bytes)
    )
    return result


def write_evidence(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")
