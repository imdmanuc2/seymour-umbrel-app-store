from __future__ import annotations
from typing import Any

def runtime_health(*, runtime_state: str, rpc_reachable: bool, rpc_healthy: bool,
                   sync: dict[str, Any] | None = None,
                   sync_analysis: dict[str, Any] | None = None,
                   storage: dict[str, Any] | None = None,
                   telemetry_stale: bool | None = None,
                   runtime_reason: str | None = None) -> dict[str, Any]:
    state = str(runtime_state or "unknown").strip().lower()
    sync = sync or {}
    sync_analysis = sync_analysis or {}
    storage = storage or {}

    def out(health_state: str, reason_code: str, summary: str, detail: str,
            recommended_action: str, destructive: bool = False) -> dict[str, Any]:
        return {
            "state": health_state,
            "reasonCode": reason_code,
            "summary": summary,
            "detail": detail,
            "recommendedAction": recommended_action,
            "destructive": destructive,
        }

    if state in {"stopped", "offline", "not-installed"}:
        return out("warning" if state != "not-installed" else "unknown",
                   f"runtime-{state}", f"Runtime is {state.replace('-', ' ')}.",
                   runtime_reason or "The managed blockchain runtime is not currently active.",
                   "start" if state in {"stopped", "offline"} else "none")
    if state in {"error", "failed"}:
        return out("critical", "runtime-error", "Runtime reported an error.",
                   runtime_reason or "The canonical runtime state indicates a failure.",
                   "diagnostics")
    if storage.get("healthy") is False:
        return out("critical", "storage-unhealthy", "Blockchain storage is unavailable.",
                   str(storage.get("error") or "The configured blockchain storage failed a health check."),
                   "inspect-storage")
    if not rpc_reachable and state not in {"starting", "recovering"}:
        return out("critical", "rpc-unreachable", "Blockchain RPC is unavailable.",
                   runtime_reason or "The runtime is active but its RPC endpoint is not reachable.",
                   "diagnostics")
    if rpc_reachable and not rpc_healthy:
        return out("warning", "rpc-degraded", "Blockchain RPC health is degraded.",
                   runtime_reason or "RPC is reachable but detailed health checks are not passing.",
                   "diagnostics")
    stall = sync_analysis.get("stall")
    if isinstance(stall, dict) and stall.get("stalled"):
        return out("warning", str(stall.get("reason") or "sync-stalled"),
                   "Blockchain synchronization appears stalled.",
                   "No block-height progress has been observed within the configured stall window.",
                   "diagnostics")
    recs = sync_analysis.get("recommendations")
    if isinstance(recs, list):
        for item in recs:
            if not isinstance(item, dict):
                continue
            code = str(item.get("code") or "")
            if code == "low-storage":
                return out("critical", "low-storage", "Blockchain storage is running low.",
                           str(item.get("message") or "Available storage is below the configured threshold."),
                           "inspect-storage")
            if code == "low-peer-count":
                return out("warning", "low-peer-count", "Blockchain peer connectivity is degraded.",
                           str(item.get("message") or "The runtime has fewer peers than expected."),
                           "diagnostics")
    if telemetry_stale:
        return out("warning", "telemetry-stale", "Runtime telemetry is stale.",
                   "The runtime may still be healthy, but current telemetry could not be refreshed.",
                   "diagnostics")
    if state in {"starting", "recovering"}:
        return out("warning", f"runtime-{state}", f"Runtime is {state}.",
                   runtime_reason or "The runtime is warming, verifying, or recovering existing state.",
                   "observe")
    if state == "syncing" or bool(sync.get("initialBlockDownload")):
        return out("healthy", "syncing", "Blockchain synchronization is progressing.",
                   "The runtime is active and initial blockchain synchronization is in progress.",
                   "observe")
    if state == "running":
        return out("healthy", "runtime-healthy", "Runtime is healthy.",
                   "The managed blockchain runtime is active and no immediate recovery action is required.",
                   "none")
    if state == "degraded":
        return out("warning", "runtime-degraded", "Runtime is degraded.",
                   runtime_reason or "The runtime is active but one or more health signals are degraded.",
                   "diagnostics")
    return out("unknown", "runtime-unknown", "Runtime health is unknown.",
               runtime_reason or "There is not enough current information to determine runtime health.",
               "diagnostics")
