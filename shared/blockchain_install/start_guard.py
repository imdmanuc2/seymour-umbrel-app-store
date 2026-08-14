from __future__ import annotations

import json
import re
import subprocess
import socket
from urllib.parse import quote
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class StorageExpectation:
    app_id: str
    compose_path: Path
    data_path: Path
    status_data_path: Path | None = None


def resolve_storage_expectation(
    *,
    data_directory: Path,
    app_id: str,
) -> StorageExpectation | None:
    compose = (
        data_directory
        / "app-data"
        / app_id
        / "docker-compose.yml"
    )

    if not compose.is_file():
        return None

    text = compose.read_text()

    data_matches = re.findall(
        r'^\s*-\s+(.+):/data(?::(?:ro|rw))?\s*$',
        text,
        flags=re.MULTILINE,
    )

    if not data_matches:
        return None

    source = (
        data_matches[0]
        .strip()
        .strip("'\"")
    )

    if "$" in source:
        raise RuntimeError(
            "Blockchain runtime storage binding "
            f"is not persisted for {app_id}; "
            "refusing start."
        )

    data_path = Path(source)

    if not data_path.is_absolute():
        raise RuntimeError(
            "Blockchain runtime /data source "
            f"is not absolute: {source}"
        )

    status_matches = re.findall(
        r'^\s*-\s+(.+):/node-data(?::(?:ro|rw))?\s*$',
        text,
        flags=re.MULTILINE,
    )

    status_data_path = None

    if status_matches:
        status_source = (
            status_matches[0]
            .strip()
            .strip("'\"")
        )

        if "$" in status_source:
            raise RuntimeError(
                "Blockchain status storage binding "
                f"is not persisted for {app_id}; "
                "refusing start."
            )

        status_data_path = Path(
            status_source
        )

        if (
            status_data_path.resolve()
            != data_path.resolve()
        ):
            raise RuntimeError(
                "Blockchain runtime /data and "
                "/node-data bindings disagree: "
                f"{data_path} != "
                f"{status_data_path}"
            )

    return StorageExpectation(
        app_id=app_id,
        compose_path=compose,
        data_path=data_path,
        status_data_path=status_data_path,
    )

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


def _docker_request(path: str) -> tuple[int, bytes]:
    docker_socket = Path("/var/run/docker.sock")

    if not docker_socket.exists():
        return 0, b""

    sock = socket.socket(
        socket.AF_UNIX,
        socket.SOCK_STREAM,
    )
    sock.settimeout(5)
    sock.connect(str(docker_socket))

    sock.sendall(
        (
            f"GET {path} HTTP/1.1\r\n"
            "Host: docker\r\n"
            "Connection: close\r\n"
            "\r\n"
        ).encode()
    )

    chunks = []

    while True:
        chunk = sock.recv(65536)

        if not chunk:
            break

        chunks.append(chunk)

    sock.close()

    raw = b"".join(chunks)
    head, _, body = raw.partition(
        b"\r\n\r\n"
    )

    try:
        status = int(
            head.splitlines()[0].split()[1]
        )
    except Exception:
        status = 0

    return status, body


def discover_node_container(
    app_id: str,
) -> str | None:
    filters = quote(
        json.dumps(
            {
                "label": [
                    (
                        "com.docker.compose.project="
                        f"{app_id}"
                    ),
                    "com.docker.compose.service=node",
                ]
            }
        ),
        safe="",
    )

    status, body = _docker_request(
        f"/containers/json?all=1&filters={filters}"
    )

    if status != 200:
        return None

    try:
        containers = json.loads(
            body.decode()
        )
    except Exception:
        return None

    if not isinstance(containers, list):
        return None

    for container in containers:
        names = container.get("Names") or []

        if names:
            return str(names[0]).lstrip("/")

    return None

def verify_live_binding(*, expectation: StorageExpectation, container_name: str) -> dict[str, Any]:
    status, body = _docker_request(
        "/containers/"
        + quote(container_name, safe="")
        + "/json"
    )

    mounts = []

    if status == 200:
        try:
            payload = json.loads(
                body.decode()
            )

            value = payload.get(
                "Mounts"
            )

            mounts = (
                value
                if isinstance(value, list)
                else []
            )
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
