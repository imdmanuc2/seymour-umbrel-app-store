from __future__ import annotations

from dataclasses import dataclass
from typing import Any

CANONICAL_RUNTIME_STATES = (
    "starting",
    "syncing",
    "running",
    "degraded",
    "stopped",
    "offline",
    "error",
    "unknown",
)

@dataclass(frozen=True)
class CanonicalRuntimeState:
    state: str
    reason: str
    installed: bool
    running: bool
    container_health: str
    rpc_reachable: bool
    rpc_healthy: bool
    rpc_status: str | None
    initial_block_download: bool | None
    verification_progress: float | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "reason": self.reason,
            "installed": self.installed,
            "running": self.running,
            "containerHealth": self.container_health,
            "rpcReachable": self.rpc_reachable,
            "rpcHealthy": self.rpc_healthy,
            "rpcStatus": self.rpc_status,
            "initialBlockDownload": self.initial_block_download,
            "verificationProgress": self.verification_progress,
        }

class RuntimeStateService:
    def normalize(self, runtime: dict[str, Any]) -> CanonicalRuntimeState:
        container = runtime.get("container") if isinstance(runtime.get("container"), dict) else {}
        rpc = runtime.get("rpc") if isinstance(runtime.get("rpc"), dict) else {}
        probe = rpc.get("probe") if isinstance(rpc.get("probe"), dict) else {}

        installed = bool(runtime.get("installed"))
        running = bool(runtime.get("running"))
        container_health = str(container.get("health", "unknown")).lower()
        rpc_reachable = bool(probe.get("reachable"))
        rpc_healthy = bool(probe.get("healthy"))
        rpc_status = str(probe.get("status", "")).lower()
        ibd = probe.get("initialBlockDownload")
        progress = probe.get("verificationProgress")

        if not installed:
            state = "offline"
            reason = "Runtime is not installed or unavailable."
        elif not running:
            state = "stopped"
            reason = "Runtime is installed but not running."
        elif container_health == "starting":
            state = "starting"
            reason = "Runtime is starting or RPC is warming up."
        elif rpc_reachable and rpc_healthy and ibd is True:
            state = "syncing"
            reason = "Runtime RPC is healthy and initial block download is active."
        elif rpc_reachable and rpc_healthy and rpc_status == "rpc-slow":
            state = "syncing"
            reason = "Runtime RPC is healthy while detailed synchronization telemetry is temporarily slow."
        elif rpc_reachable and rpc_healthy:
            state = "running"
            reason = "Runtime RPC is healthy."
        elif running:
            state = "degraded"
            reason = "Runtime is running but one or more canonical health signals are degraded."
        else:
            state = "unknown"
            reason = "Canonical runtime state cannot be determined."

        return CanonicalRuntimeState(
            state=state,
            reason=reason,
            installed=installed,
            running=running,
            container_health=container_health,
            rpc_reachable=rpc_reachable,
            rpc_healthy=rpc_healthy,
            rpc_status=rpc_status or None,
            initial_block_download=ibd if isinstance(ibd, bool) else None,
            verification_progress=float(progress) if isinstance(progress, (int, float)) else None,
        )

    def normalize_dict(self, runtime: dict[str, Any]) -> dict[str, Any]:
        return self.normalize(runtime).to_dict()

DEFAULT_RUNTIME_STATE_SERVICE = RuntimeStateService()

def normalize_runtime_state(runtime: dict[str, Any]) -> dict[str, Any]:
    return DEFAULT_RUNTIME_STATE_SERVICE.normalize_dict(runtime)
