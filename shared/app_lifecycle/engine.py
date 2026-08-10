from __future__ import annotations
from .model import LIFECYCLE_ACTIONS, LIFECYCLE_STATES, LifecyclePlan, LifecycleState

_TARGET_STATE = {
    "install": "installing",
    "start": "starting",
    "stop": "stopped",
    "restart": "restarting",
    "update": "updating",
    "uninstall": "uninstalling",
}

_ALLOWED = {
    "not-installed": {"install"},
    "installing": set(),
    "stopped": {"start", "update", "uninstall"},
    "starting": set(),
    "running": {"stop", "restart", "update", "uninstall"},
    "restarting": set(),
    "updating": set(),
    "uninstalling": set(),
    "degraded": {"stop", "restart", "update", "uninstall"},
    "error": {"start", "stop", "restart", "update", "uninstall"},
    "unknown": set(),
}

class AppLifecycleEngine:
    def normalize_state(
        self,
        *,
        app_id: str,
        installed: bool,
        running: bool,
        native_state: str | None = None,
        healthy: bool | None = None,
        version: str | None = None,
        update_available: bool | None = None,
        detail: dict | None = None,
    ) -> LifecycleState:
        raw = str(native_state or "").strip().lower()
        aliases = {
            "ready": "running",
            "online": "running",
            "active": "running",
            "started": "running",
            "inactive": "stopped",
            "offline": "stopped",
            "not_installed": "not-installed",
            "not installed": "not-installed",
            "failed": "error",
            "unhealthy": "degraded",
        }
        state = aliases.get(raw, raw)

        if not installed:
            state = "not-installed"
        elif state not in LIFECYCLE_STATES:
            if running and healthy is False:
                state = "degraded"
            elif running:
                state = "running"
            else:
                state = "stopped"

        if state == "running" and healthy is False:
            state = "degraded"

        return LifecycleState(
            app_id=app_id,
            state=state,
            installed=installed,
            running=running,
            healthy=healthy,
            version=version,
            update_available=update_available,
            detail=detail or {},
        )

    def capabilities(self, state: LifecycleState) -> dict[str, bool]:
        allowed = _ALLOWED.get(state.state, set())
        return {action: action in allowed for action in LIFECYCLE_ACTIONS}

    def confirmation_token(self, action: str, app_id: str) -> str:
        return f"{action.upper()}-{app_id}"

    def plan(self, state: LifecycleState, action: str) -> LifecyclePlan:
        action = str(action).strip().lower()

        if action not in LIFECYCLE_ACTIONS:
            return LifecyclePlan(
                app_id=state.app_id,
                action=action,
                current_state=state.state,
                allowed=False,
                reason="Unsupported lifecycle action.",
                requires_confirmation=False,
                confirmation_token=None,
                target_state=None,
            )

        allowed = action in _ALLOWED.get(state.state, set())

        return LifecyclePlan(
            app_id=state.app_id,
            action=action,
            current_state=state.state,
            allowed=allowed,
            reason=(
                f"{action} is allowed while {state.app_id} is {state.state}."
                if allowed
                else f"{action} is not allowed while {state.app_id} is {state.state}."
            ),
            requires_confirmation=allowed,
            confirmation_token=(
                self.confirmation_token(action, state.app_id)
                if allowed else None
            ),
            target_state=_TARGET_STATE.get(action) if allowed else None,
        )
