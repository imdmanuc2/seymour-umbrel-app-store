from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import platform
import shutil
import socket
import subprocess
import time
from typing import Any
from urllib import request
from bch_runtime_probe import probe as probe_bch_runtime
from runtime_registry import dashboard_runtimes
from runtime_health import runtime_health


BCH_APP_ID = os.environ.get("BCH_APP_ID", "seymour-bch-node")
BCH_HEALTH_URL = os.environ.get(
    "BCH_HEALTH_URL",
    "http://seymour-bch-node_status_1:8080/api/health",
)
BCH_STATUS_URL = os.environ.get(
    "BCH_STATUS_URL",
    "http://seymour-bch-node_status_1:8080/api/status",
)
BCH_DATA_PATH = Path(
    os.environ.get(
        "BCH_DATA_PATH",
        "/bch-data",
    )
)
DOCKER_SOCKET = Path(
    os.environ.get(
        "DOCKER_SOCKET",
        "/var/run/docker.sock",
    )
)


def read_json_url(url: str, timeout: float = 3.0) -> dict[str, Any]:
    try:
        with request.urlopen(url, timeout=timeout) as response:
            return json.loads(response.read().decode())
    except Exception as exc:
        return {
            "reachable": False,
            "error": str(exc),
            "url": url,
        }


def read_meminfo() -> dict[str, int]:
    values: dict[str, int] = {}

    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            key, raw = line.split(":", 1)
            amount = int(raw.strip().split()[0]) * 1024
            values[key] = amount
    except Exception:
        return {
            "totalBytes": 0,
            "availableBytes": 0,
            "usedBytes": 0,
            "usedPercent": 0,
        }

    total = values.get("MemTotal", 0)
    available = values.get("MemAvailable", 0)
    used = max(total - available, 0)
    percent = round((used / total) * 100, 2) if total else 0

    return {
        "totalBytes": total,
        "availableBytes": available,
        "usedBytes": used,
        "usedPercent": percent,
    }


def read_cpu_percent() -> float:
    def sample() -> tuple[int, int]:
        parts = Path("/proc/stat").read_text().splitlines()[0].split()
        values = [int(value) for value in parts[1:]]
        idle = values[3] + values[4]
        total = sum(values)
        return idle, total

    try:
        idle1, total1 = sample()
        time.sleep(0.12)
        idle2, total2 = sample()
        idle_delta = idle2 - idle1
        total_delta = total2 - total1

        if total_delta <= 0:
            return 0.0

        return round(
            100.0 * (1.0 - idle_delta / total_delta),
            2,
        )
    except Exception:
        return 0.0


def docker_available() -> bool:
    if not DOCKER_SOCKET.exists():
        return False

    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(2)
        sock.connect(str(DOCKER_SOCKET))
        sock.close()
        return True
    except Exception:
        return False


def docker_container(name: str) -> dict[str, Any]:
    if not docker_available():
        return {
            "found": False,
            "running": False,
            "health": "unknown",
            "status": "docker-unavailable",
        }

    try:
        result = subprocess.run(
            [
                "docker",
                "inspect",
                name,
                "--format",
                (
                    '{"status":"{{.State.Status}}",'
                    '"running":{{.State.Running}},'
                    '"exitCode":{{.State.ExitCode}},'
                    '"restartCount":{{.RestartCount}},'
                    '"image":"{{.Config.Image}}",'
                    '"health":"{{if .State.Health}}'
                    '{{.State.Health.Status}}{{else}}none{{end}}"}'
                ),
            ],
            capture_output=True,
            text=True,
            timeout=4,
            check=False,
        )

        if result.returncode != 0:
            return {
                "found": False,
                "running": False,
                "health": "unknown",
                "status": "not-found",
                "error": result.stderr.strip(),
            }

        payload = json.loads(result.stdout.strip())
        payload["found"] = True
        return payload
    except Exception as exc:
        return {
            "found": False,
            "running": False,
            "health": "unknown",
            "status": "error",
            "error": str(exc),
        }


def storage_payload(path: Path) -> dict[str, Any]:
    target = path if path.exists() else Path("/")

    try:
        usage = shutil.disk_usage(target)
        used_percent = (
            round((usage.used / usage.total) * 100, 2)
            if usage.total
            else 0
        )
        return {
            "path": str(target),
            "totalBytes": usage.total,
            "usedBytes": usage.used,
            "freeBytes": usage.free,
            "usedPercent": used_percent,
        }
    except Exception as exc:
        return {
            "path": str(target),
            "totalBytes": 0,
            "usedBytes": 0,
            "freeBytes": 0,
            "usedPercent": 0,
            "error": str(exc),
        }


def directory_size(path: Path) -> int:
    if not path.exists():
        return 0

    total = 0

    try:
        for item in path.rglob("*"):
            if item.is_file():
                total += item.stat().st_size
    except Exception:
        return total

    return total


def host_telemetry() -> dict[str, Any]:
    storage = storage_payload(Path("/"))
    docker_ok = docker_available()

    return {
        "hostname": socket.gethostname(),
        "architecture": platform.machine(),
        "platform": platform.platform(),
        "cpuCount": os.cpu_count() or 0,
        "cpuPercent": read_cpu_percent(),
        "memory": read_meminfo(),
        "storage": storage,
        "docker": {
            "available": docker_ok,
            "socket": str(DOCKER_SOCKET),
        },
        "healthy": (
            docker_ok
            and storage.get("freeBytes", 0) > 0
        ),
    }


def normalized_sync(status: dict[str, Any]) -> dict[str, Any]:
    height = (
        status.get("blocks")
        or status.get("height")
        or status.get("blockHeight")
    )
    headers = (
        status.get("headers")
        or status.get("headerHeight")
        or height
    )
    progress = (
        status.get("verificationprogress")
        or status.get("verificationProgress")
        or status.get("syncProgress")
    )

    if progress is not None:
        try:
            progress = float(progress)
            if progress <= 1:
                progress *= 100
            progress = round(progress, 4)
        except Exception:
            progress = None

    if progress is None and height and headers:
        try:
            progress = round(
                min(float(height) / float(headers), 1.0) * 100,
                4,
            )
        except Exception:
            progress = None

    return {
        "height": height,
        "headers": headers,
        "progressPercent": progress,
        "initialBlockDownload": (
            status.get("initialblockdownload")
            or status.get("initialBlockDownload")
            or False
        ),
    }


def bch_telemetry() -> dict[str, Any]:
    # Project the canonical BCH runtime probe into the dashboard contract.
    runtime = probe_bch_runtime()

    operational_state = (
        runtime.get("operationalState")
        if isinstance(runtime.get("operationalState"), dict)
        else {}
    )
    rpc = runtime.get("rpc") if isinstance(runtime.get("rpc"), dict) else {}
    rpc_probe = rpc.get("probe") if isinstance(rpc.get("probe"), dict) else {}
    legacy_status = rpc.get("status") if isinstance(rpc.get("status"), dict) else {}
    legacy_payload = (
        legacy_status.get("payload")
        if isinstance(legacy_status.get("payload"), dict)
        else {}
    )

    runtime_state = operational_state.get("state") or runtime.get("lifecycleStatus") or "unknown"

    # Container/runtime presence is authoritative for terminal lifecycle state.
    # Slow or cached RPC telemetry may describe an earlier syncing state, but it
    # must not make a stopped managed app appear to still be running.
    installed = bool(runtime.get("installed"))
    running = bool(runtime.get("running"))
    if not installed:
        runtime_state = "not-installed"
    elif not running:
        runtime_state = "stopped"

    progress = rpc_probe.get("progressPercent")
    if progress is None:
        verification = operational_state.get("verificationProgress")
        if isinstance(verification, (int, float)):
            progress = float(verification) * 100.0

    sync = {
        "height": rpc_probe.get("height"),
        "headers": rpc_probe.get("headers"),
        "progressPercent": progress,
        "initialBlockDownload": (
            rpc_probe.get("initialBlockDownload")
            if rpc_probe.get("initialBlockDownload") is not None
            else operational_state.get("initialBlockDownload")
        ),
    }

    storage = legacy_payload.get("storage") if isinstance(legacy_payload.get("storage"), dict) else {}
    used_bytes = storage.get("usedBytes")
    if used_bytes is None:
        used_bytes = directory_size(BCH_DATA_PATH)

    rpc_reachable = bool(
        operational_state.get("rpcReachable")
        if operational_state.get("rpcReachable") is not None
        else rpc_probe.get("reachable")
    )
    rpc_healthy = bool(
        operational_state.get("rpcHealthy")
        if operational_state.get("rpcHealthy") is not None
        else rpc_probe.get("healthy")
    )

    health = runtime_health(
        runtime_state=runtime_state,
        rpc_reachable=rpc_reachable,
        rpc_healthy=rpc_healthy,
        sync=sync,
        sync_analysis={},
        storage=storage,
        telemetry_stale=bool(runtime.get("telemetryStale")),
        runtime_reason=operational_state.get("reason"),
    )

    return {
        "providerId": "bitcoin-cash-mainnet",
        "appId": runtime.get("appId", BCH_APP_ID),
        "installed": installed,
        "running": running,
        "lifecycleStatus": runtime_state,
        "runtimeState": runtime_state,
        "runtimeStateReason": operational_state.get("reason"),
        "health": health,
        "telemetryFresh": runtime.get("telemetryFresh"),
        "telemetryStale": runtime.get("telemetryStale"),
        "telemetryAgeSeconds": runtime.get("telemetryAgeSeconds"),
        "telemetrySource": runtime.get("telemetrySource"),
        "telemetryCacheHit": runtime.get("telemetryCacheHit"),
        "telemetryCacheAgeSeconds": runtime.get("telemetryCacheAgeSeconds"),
        "runtimeRpcReachable": rpc_reachable,
        "runtimeRpcHealthy": rpc_healthy,
        "runtimeInitialBlockDownload": sync["initialBlockDownload"],
        "runtimeVerificationProgress": operational_state.get("verificationProgress"),
        "operationalState": operational_state,
        "container": runtime.get("container", {}),
        "rpc": {
            "reachable": rpc_reachable,
            "healthy": rpc_healthy,
            "probe": rpc_probe,
        },
        "sync": sync,
        "peers": rpc_probe.get("peers"),
        "mempool": None,
        "data": {
            "path": str(BCH_DATA_PATH),
            "usedBytes": used_bytes,
        },
    }


def dashboard_payload() -> dict[str, Any]:
    return {
        "generatedAt": time.time(),
        "host": host_telemetry(),
        "providers": dashboard_runtimes(
            bch_telemetry=bch_telemetry,
        ),
    }
