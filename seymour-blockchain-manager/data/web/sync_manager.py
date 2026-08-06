from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import time
from typing import Any

HISTORY_PATH = Path(os.environ.get("SYNC_HISTORY_PATH", "/evidence/sync-history.jsonl"))
STALL_SECONDS = int(os.environ.get("SYNC_STALL_SECONDS", "600"))
LOW_PEER_THRESHOLD = int(os.environ.get("SYNC_LOW_PEERS", "3"))
LOW_DISK_BYTES = int(os.environ.get("SYNC_LOW_DISK_BYTES", str(50 * 1000**3)))


@dataclass
class SyncSnapshot:
    captured_at: float
    height: int | None
    headers: int | None
    progress_percent: float | None
    peers: int | None
    free_bytes: int | None
    rpc_reachable: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def append_history(snapshot: SyncSnapshot) -> None:
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with HISTORY_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(snapshot.to_dict(), sort_keys=True) + "\n")


def read_history(limit: int = 120) -> list[dict[str, Any]]:
    if not HISTORY_PATH.is_file():
        return []
    result = []
    for line in HISTORY_PATH.read_text().splitlines()[-limit:]:
        try:
            result.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return result


def _int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def snapshot_from_dashboard(dashboard: dict[str, Any]) -> SyncSnapshot:
    provider = dashboard.get("providers", {}).get("bitcoin-cash-mainnet", {})
    sync = provider.get("sync", {})
    storage = dashboard.get("host", {}).get("storage", {})
    return SyncSnapshot(
        captured_at=time.time(),
        height=_int(sync.get("height")),
        headers=_int(sync.get("headers")),
        progress_percent=_float(sync.get("progressPercent")),
        peers=_int(provider.get("peers")),
        free_bytes=_int(storage.get("freeBytes")),
        rpc_reachable=bool(provider.get("rpc", {}).get("reachable")),
    )


def blocks_remaining(snapshot: SyncSnapshot) -> int | None:
    if snapshot.height is None or snapshot.headers is None:
        return None
    return max(snapshot.headers - snapshot.height, 0)


def blocks_per_second(history: list[dict[str, Any]], current: SyncSnapshot) -> float | None:
    candidates = [
        item for item in history
        if item.get("height") is not None
        and item.get("captured_at") is not None
        and float(item["captured_at"]) < current.captured_at
    ]
    if not candidates or current.height is None:
        return None
    previous = candidates[-1]
    elapsed = current.captured_at - float(previous["captured_at"])
    delta = current.height - int(previous["height"])
    if elapsed <= 0 or delta < 0:
        return None
    return round(delta / elapsed, 4)


def eta_seconds(remaining: int | None, rate: float | None) -> int | None:
    if remaining is None or rate is None or rate <= 0:
        return None
    return int(remaining / rate)


def peer_quality(peers: int | None) -> dict[str, Any]:
    if peers is None:
        return {"state": "unknown", "score": 0}
    if peers >= 8:
        return {"state": "good", "score": 100}
    if peers >= LOW_PEER_THRESHOLD:
        return {"state": "degraded", "score": 60}
    return {"state": "poor", "score": 20}


def detect_stall(history: list[dict[str, Any]], current: SyncSnapshot) -> dict[str, Any]:
    if current.height is None:
        return {"stalled": True, "reason": "height-unavailable"}
    same_height = [
        item for item in history
        if item.get("height") == current.height and item.get("captured_at") is not None
    ]
    if not same_height:
        return {"stalled": False, "reason": None}
    earliest = min(float(item["captured_at"]) for item in same_height)
    elapsed = current.captured_at - earliest
    return {
        "stalled": elapsed >= STALL_SECONDS,
        "reason": "no-height-progress" if elapsed >= STALL_SECONDS else None,
        "secondsWithoutProgress": int(elapsed),
    }


def recommendations(snapshot: SyncSnapshot, stall: dict[str, Any]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    if not snapshot.rpc_reachable:
        result.append({"severity": "critical", "code": "rpc-unreachable", "message": "Check the BCH container and RPC configuration."})
    if snapshot.peers is not None and snapshot.peers < LOW_PEER_THRESHOLD:
        result.append({"severity": "warning", "code": "low-peer-count", "message": "Check DNS, firewall rules, and outbound connectivity."})
    if snapshot.free_bytes is not None and snapshot.free_bytes < LOW_DISK_BYTES:
        result.append({"severity": "critical", "code": "low-storage", "message": "Free storage before synchronization continues."})
    if stall.get("stalled"):
        result.append({"severity": "warning", "code": "sync-stalled", "message": "Review recent logs and consider a guarded restart."})
    if not result:
        result.append({"severity": "info", "code": "sync-healthy", "message": "Synchronization is progressing normally."})
    return result


def analyze(dashboard: dict[str, Any]) -> dict[str, Any]:
    history = read_history()
    current = snapshot_from_dashboard(dashboard)
    remaining = blocks_remaining(current)
    rate = blocks_per_second(history, current)
    stall = detect_stall(history, current)
    append_history(current)
    return {
        "generatedAt": utc_now(),
        "providerId": "bitcoin-cash-mainnet",
        "snapshot": current.to_dict(),
        "blocksRemaining": remaining,
        "blocksPerSecond": rate,
        "etaSeconds": eta_seconds(remaining, rate),
        "peerQuality": peer_quality(current.peers),
        "stall": stall,
        "recommendations": recommendations(current, stall),
        "historyPoints": len(history) + 1,
    }
