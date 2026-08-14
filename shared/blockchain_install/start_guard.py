from __future__ import annotations

import json
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class StorageExpectation:
    app_id: str
    compose_path: Path
    data_path: Path


def resolve_storage_expectation(*, data_directory: Path, app_id: str) -> StorageExpectation | None:
    compose = data_directory / "app-data" / app_id / "docker-compose.yml"
    if not compose.is_file():
        return None
    text = compose.read_text()
    matches = re.findall(
        r'^\s*-\s+(.+):/data(?::(?:ro|rw))?\s*$',
        text,
        flags=re.MULTILINE,
    )
    if not matches:
        return None
    source = matches[0].strip().strip("'\\\"")
    if "$" in source:
        raise RuntimeError(
            f"Blockchain runtime storage binding is not persisted for {app_id}; refusing start."
        )
    path = Path(source)
    if not path.is_absolute():
        raise RuntimeError(f"Blockchain runtime /data source is not absolute: {source}")
    return StorageExpectation(app_id=app_id, compose_path=compose, data_path=path)


def verify_expected_path(expectation: StorageExpectation) -> dict[str, Any]:
    path = expectation.data_path
    result = {
        "appId": expectation.app_id,
        "dataPath": str(path),
        "exists": path.exists(),
        "healthy": False,
        "mount": None,
        "error": None,
    }
    if not path.is_dir():
        result["error"] = "expected-data-path-missing"
        return result

    if str(path).startswith("/mnt/"):
        probe = subprocess.run(
            ["findmnt", "-J", "-T", str(path)],
            capture_output=True, text=True, timeout=10, check=False,
        )
        if probe.returncode != 0 or not probe.stdout.strip():
            result["error"] = "storage-mount-not-found"
            return result
        try:
            fs = json.loads(probe.stdout)["filesystems"][0]
            mount = {
                "target": fs.get("target"),
                "source": fs.get("source"),
                "fstype": fs.get("fstype"),
            }
        except Exception:
            result["error"] = "storage-mount-probe-invalid"
            return result
        result["mount"] = mount
        if mount.get("target") == "/":
            result["error"] = "storage-false-mount-root-fallback"
            return result

    result["healthy"] = True
    return result


def discover_node_container(app_id: str) -> str | None:
    proc = subprocess.run(
        [
            "docker", "ps", "-a",
            "--filter", f"label=com.docker.compose.project={app_id}",
            "--filter", "label=com.docker.compose.service=node",
            "--format", "{{.Names}}",
        ],
        capture_output=True, text=True, timeout=10, check=False,
    )
    if proc.returncode != 0:
        return None
    names = [x.strip() for x in proc.stdout.splitlines() if x.strip()]
    return names[0] if names else None


def verify_live_binding(*, expectation: StorageExpectation, container_name: str) -> dict[str, Any]:
    proc = subprocess.run(
        ["docker", "inspect", container_name, "--format", "{{json .Mounts}}"],
        capture_output=True, text=True, timeout=10, check=False,
    )
    mounts = []
    if proc.returncode == 0:
        try:
            value = json.loads(proc.stdout.strip())
            mounts = value if isinstance(value, list) else []
        except Exception:
            pass

    actual = next(
        (m.get("Source") for m in mounts if isinstance(m, dict) and m.get("Destination") == "/data"),
        None,
    )
    expected = str(expectation.data_path.resolve())
    actual_resolved = str(Path(actual).resolve()) if actual else None
    matches = bool(actual_resolved == expected)
    return {
        "appId": expectation.app_id,
        "container": container_name,
        "expectedDataPath": expected,
        "actualDataPath": actual_resolved,
        "healthy": matches,
        "matches": matches,
        "error": None if matches else "storage-binding-mismatch",
    }


def wait_for_live_binding(*, expectation: StorageExpectation,
                          timeout_seconds: int = 60,
                          interval_seconds: int = 2) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    latest = {"healthy": False, "error": "node-container-not-found"}
    while time.monotonic() < deadline:
        name = discover_node_container(expectation.app_id)
        if name:
            latest = verify_live_binding(expectation=expectation, container_name=name)
            return latest
        time.sleep(interval_seconds)
    return latest
