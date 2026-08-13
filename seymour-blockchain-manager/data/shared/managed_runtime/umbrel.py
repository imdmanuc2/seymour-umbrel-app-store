from __future__ import annotations
from typing import Any

from shared.app_lifecycle import AppLifecycleEngine
from shared.runtime_state import RuntimeStateService
from .adapter import ManagedRuntimeAdapter
from .models import ManagedRuntimeCapabilities, ManagedRuntimeIdentity, ManagedRuntimeObservation

def _mapping(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if hasattr(value, "to_dict"):
        value = value.to_dict()
    if hasattr(value, "as_dict"):
        value = value.as_dict()
    return dict(value) if isinstance(value, dict) else {}

class UmbrelManagedRuntimeAdapter(ManagedRuntimeAdapter):
    adapter_type = "umbrel"

    def __init__(self, runtime: Any, *,
                 runtime_state_service: RuntimeStateService | None = None,
                 lifecycle_engine: AppLifecycleEngine | None = None,
                 lifecycle_service: Any | None = None,
                 state_probes: dict[str, Any] | None = None) -> None:
        self.runtime = runtime
        self.runtime_state_service = runtime_state_service or RuntimeStateService()
        self.lifecycle_engine = lifecycle_engine or AppLifecycleEngine()
        self.lifecycle_service = lifecycle_service
        self.state_probes = dict(state_probes or {})

    def supports(self, runtime_id: str) -> bool:
        try:
            return bool(self.runtime.installed(runtime_id) or self.runtime.source_available(runtime_id))
        except Exception:
            return False

    @staticmethod
    def _container_projection(native: dict[str, Any]) -> dict[str, Any]:
        containers = native.get("containers")
        if not isinstance(containers, list) or not containers:
            return {"health": "unknown"}
        running = [x for x in containers if isinstance(x, dict) and x.get("running") is True]
        selected = running[0] if running else containers[0]
        if not isinstance(selected, dict):
            return {"health": "unknown"}
        healthy = selected.get("healthy")
        status = str(selected.get("status") or "").lower()
        health = "healthy" if healthy is True else "unhealthy" if healthy is False else "starting" if "starting" in status else "unknown"
        return {
            "health": health,
            "name": selected.get("name"),
            "service": selected.get("service"),
            "status": selected.get("status"),
        }

    def _canonical_input(self, runtime_id: str, native: dict[str, Any]) -> dict[str, Any]:
        containers = native.get("containers")
        running = isinstance(containers, list) and any(
            isinstance(x, dict) and x.get("running") is True for x in containers
        )
        canonical = {
            "installed": bool(native.get("installed")),
            "running": bool(running),
            "container": self._container_projection(native),
            "rpc": {"probe": {}},
        }
        probe = self.state_probes.get(runtime_id)
        if probe is not None:
            raw = _mapping(probe())
            op = raw.get("operationalState")
            op = op if isinstance(op, dict) else {}
            canonical["rpc"]["probe"] = {
                "reachable": op.get("rpcReachable"),
                "healthy": op.get("rpcHealthy"),
                "status": op.get("rpcStatus"),
                "initialBlockDownload": op.get("initialBlockDownload"),
                "verificationProgress": op.get("verificationProgress"),
            }
        return canonical

    def _capabilities(self, runtime_id: str, state: dict[str, Any]) -> ManagedRuntimeCapabilities:
        lifecycle_state = self.lifecycle_engine.normalize_state(
            app_id=runtime_id,
            installed=bool(state.get("installed")),
            running=bool(state.get("running")),
            native_state=str(state.get("state") or "unknown"),
            healthy=True if state.get("state") == "running" else False if state.get("state") in {"degraded", "error"} else None,
        )
        allowed = self.lifecycle_engine.capabilities(lifecycle_state)
        return ManagedRuntimeCapabilities(
            inspect=True,
            telemetry=True,
            logs=hasattr(self.runtime, "collect_logs"),
            install=bool(allowed.get("install")),
            start=bool(allowed.get("start")),
            stop=bool(allowed.get("stop")),
            restart=bool(allowed.get("restart")),
            update=bool(allowed.get("update")),
            uninstall=bool(allowed.get("uninstall")),
        )

    def inspect(self, runtime_id: str, *, provider_id: str | None = None,
                display_name: str | None = None) -> ManagedRuntimeObservation:
        native = _mapping(self.runtime.inspect_app(runtime_id))
        state = self.runtime_state_service.normalize_dict(
            self._canonical_input(runtime_id, native)
        )
        identity = ManagedRuntimeIdentity(
            runtime_id=runtime_id,
            runtime_type=self.adapter_type,
            provider_id=provider_id,
            display_name=display_name,
            version=str(native.get("version")) if native.get("version") is not None else None,
        )
        telemetry = {
            "health": _mapping(native.get("health")),
            "dependencies": list(native.get("dependencies") or []),
            "missingDependencies": list(native.get("missing_dependencies") or []),
            "errors": list(native.get("errors") or []),
        }
        return ManagedRuntimeObservation(
            identity=identity,
            state=state,
            capabilities=self._capabilities(runtime_id, state),
            telemetry=telemetry,
            native=native,
        )

    def logs(self, runtime_id: str, *, tail: int = 200) -> Any:
        if not hasattr(self.runtime, "collect_logs"):
            return super().logs(runtime_id, tail=tail)
        try:
            return self.runtime.collect_logs(runtime_id, tail=tail)
        except TypeError:
            return self.runtime.collect_logs(runtime_id)

    def lifecycle(self, runtime_id: str, action: str, *, execute: bool = False,
                  confirmation: str | None = None,
                  correlation_id: str | None = None) -> Any:
        if self.lifecycle_service is None:
            return super().lifecycle(runtime_id, action, execute=execute,
                                     confirmation=confirmation,
                                     correlation_id=correlation_id)
        return self.lifecycle_service.request(
            runtime_id, action, execute=execute, confirmation=confirmation,
            correlation_id=correlation_id
        )
