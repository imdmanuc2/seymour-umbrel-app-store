from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .engine import AppLifecycleEngine
from .model import LifecycleState


_RUNNING_STATES = {"ready", "running", "online", "active", "started"}
_STOPPED_STATES = {"stopped", "not-running", "inactive", "offline"}
_NOT_INSTALLED_STATES = {"not-installed", "not_installed", "not installed", "missing"}


def _unwrap(payload: Any) -> Any:
    """Unwrap ControlOperation/result-style payloads without coupling to bridge classes."""
    if hasattr(payload, "result"):
        payload = payload.result
    while isinstance(payload, dict) and "result" in payload and len(payload) <= 8:
        nested = payload.get("result")
        if nested is payload:
            break
        payload = nested
    return payload


def _first(mapping: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in mapping:
            return mapping[key]
    return None


def native_state_snapshot(app_id: str, payload: Any, engine: AppLifecycleEngine) -> LifecycleState:
    """Convert a native Umbrel state payload into the SBP-030 lifecycle model."""
    value = _unwrap(payload)
    data = value if isinstance(value, dict) else {"state": value}

    raw_state = str(_first(data, "state", "status", "lifecycleState") or "unknown").strip().lower()

    installed_value = _first(data, "installed", "isInstalled")
    if isinstance(installed_value, bool):
        installed = installed_value
    elif raw_state in _NOT_INSTALLED_STATES:
        installed = False
    else:
        installed = True

    running_value = _first(data, "running", "isRunning")
    if isinstance(running_value, bool):
        running = running_value
    else:
        running = raw_state in _RUNNING_STATES

    healthy_value = _first(data, "healthy", "isHealthy")
    healthy = healthy_value if isinstance(healthy_value, bool) else None

    version = _first(data, "version", "appVersion", "installedVersion")
    update_available = _first(data, "updateAvailable", "update_available")
    if not isinstance(update_available, bool):
        update_available = None

    if raw_state in _STOPPED_STATES:
        running = False

    return engine.normalize_state(
        app_id=app_id,
        installed=installed,
        running=running,
        native_state=raw_state,
        healthy=healthy,
        version=str(version) if version is not None else None,
        update_available=update_available,
        detail={"native": data},
    )


@dataclass(frozen=True)
class LifecycleExecutionResult:
    app_id: str
    action: str
    allowed: bool
    executed: bool
    success: bool | None
    reason: str
    confirmation_token: str | None
    before: dict[str, Any]
    after: dict[str, Any] | None
    native_operation: dict[str, Any] | None
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class LifecycleExecutor:
    """Canonical adapter from lifecycle planning to the existing native Umbrel bridge."""

    def __init__(
        self,
        bridge: Any,
        engine: AppLifecycleEngine | None = None,
        state_provider: Any | None = None,
    ) -> None:
        self.bridge = bridge
        self.engine = engine or AppLifecycleEngine()
        self.state_provider = state_provider

    def read_state(self, app_id: str) -> LifecycleState:
        if self.state_provider is not None:
            canonical = self.state_provider.read_state(app_id, self.engine)
            if canonical is not None:
                return canonical
        operation = self.bridge.execute("state", app_id)
        return native_state_snapshot(app_id, operation, self.engine)

    @staticmethod
    def _operation_dict(operation: Any) -> dict[str, Any] | None:
        if operation is None:
            return None
        if hasattr(operation, "to_dict"):
            return operation.to_dict()
        if isinstance(operation, dict):
            return operation
        return {"result": str(operation)}

    def execute(
        self,
        app_id: str,
        action: str,
        *,
        execute: bool = False,
        confirmation: str | None = None,
    ) -> LifecycleExecutionResult:
        before = self.read_state(app_id)
        plan = self.engine.plan(before, action)

        if not plan.allowed:
            return LifecycleExecutionResult(
                app_id=app_id,
                action=action,
                allowed=False,
                executed=False,
                success=False,
                reason=plan.reason,
                confirmation_token=None,
                before=before.as_dict(),
                after=None,
                native_operation=None,
                error=None,
            )

        if not execute:
            return LifecycleExecutionResult(
                app_id=app_id,
                action=action,
                allowed=True,
                executed=False,
                success=None,
                reason=plan.reason,
                confirmation_token=plan.confirmation_token,
                before=before.as_dict(),
                after=None,
                native_operation=None,
                error=None,
            )

        if confirmation != plan.confirmation_token:
            return LifecycleExecutionResult(
                app_id=app_id,
                action=action,
                allowed=True,
                executed=False,
                success=False,
                reason="Lifecycle write confirmation mismatch.",
                confirmation_token=plan.confirmation_token,
                before=before.as_dict(),
                after=None,
                native_operation=None,
                error=f"Expected confirmation token: {plan.confirmation_token}",
            )

        operation = self.bridge.execute(
            action,
            app_id,
            execute=True,
            confirmation=confirmation,
        )
        operation_dict = self._operation_dict(operation)
        operation_success = getattr(operation, "success", None)
        if operation_success is None and isinstance(operation_dict, dict):
            operation_success = operation_dict.get("success")
        operation_error = getattr(operation, "error", None)
        if operation_error is None and isinstance(operation_dict, dict):
            operation_error = operation_dict.get("error")

        after: LifecycleState | None = None
        try:
            after = self.read_state(app_id)
        except Exception as exc:  # native bridge result remains authoritative
            if not operation_error:
                operation_error = f"Post-action lifecycle state read failed: {exc}"

        return LifecycleExecutionResult(
            app_id=app_id,
            action=action,
            allowed=True,
            executed=True,
            success=bool(operation_success),
            reason=(
                f"{action} completed through the native Umbrel lifecycle bridge."
                if operation_success
                else f"{action} failed through the native Umbrel lifecycle bridge."
            ),
            confirmation_token=plan.confirmation_token,
            before=before.as_dict(),
            after=after.as_dict() if after else None,
            native_operation=operation_dict,
            error=str(operation_error) if operation_error else None,
        )
