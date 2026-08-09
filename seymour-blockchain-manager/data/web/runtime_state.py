from __future__ import annotations

from typing import Any

VALID_RUNTIME_STATES = {
    "not-installed",
    "stopped",
    "starting",
    "syncing",
    "healthy",
    "degraded",
}


def normalize_runtime_state(
    runtime: dict[str, Any],
) -> dict[str, Any]:
    container = (
        runtime.get("container")
        if isinstance(runtime.get("container"), dict)
        else {}
    )
    rpc = (
        runtime.get("rpc")
        if isinstance(runtime.get("rpc"), dict)
        else {}
    )
    probe = (
        rpc.get("probe")
        if isinstance(rpc.get("probe"), dict)
        else {}
    )

    installed = bool(runtime.get("installed"))
    running = bool(runtime.get("running"))
    container_health = str(
        container.get("health", "unknown")
    ).lower()
    rpc_reachable = bool(probe.get("reachable"))
    rpc_healthy = bool(probe.get("healthy"))
    rpc_status = str(
        probe.get("status", "")
    ).lower()
    ibd = probe.get("initialBlockDownload")
    progress = probe.get("verificationProgress")

    if not installed:
        state = "not-installed"
        reason = "Runtime is not installed."
    elif not running:
        state = "stopped"
        reason = "Runtime container is not running."
    elif container_health == "starting":
        state = "starting"
        reason = "Runtime is starting or RPC is warming up."
    elif rpc_reachable and rpc_healthy and ibd is True:
        state = "syncing"
        reason = (
            "Runtime RPC is healthy and initial block "
            "download is active."
        )
    elif (
        rpc_reachable
        and rpc_healthy
        and rpc_status == "rpc-slow"
    ):
        state = "syncing"
        reason = (
            "Runtime RPC liveness is healthy while detailed "
            "synchronization telemetry is temporarily slow."
        )
    elif rpc_reachable and rpc_healthy:
        state = "healthy"
        reason = "Runtime RPC is healthy."
    else:
        state = "degraded"
        reason = (
            "Runtime is running but one or more health "
            "signals are degraded."
        )

    return {
        "state": state,
        "reason": reason,
        "installed": installed,
        "running": running,
        "containerHealth": container_health,
        "rpcReachable": rpc_reachable,
        "rpcHealthy": rpc_healthy,
        "rpcStatus": rpc_status or None,
        "initialBlockDownload": ibd,
        "verificationProgress": progress,
    }
