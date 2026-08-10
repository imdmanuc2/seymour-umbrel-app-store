from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Any

LIFECYCLE_ACTIONS = (
    "install", "start", "stop", "restart", "update", "uninstall",
)

LIFECYCLE_STATES = (
    "not-installed", "installing", "stopped", "starting", "running",
    "restarting", "updating", "uninstalling", "degraded", "error", "unknown",
)

@dataclass(frozen=True)
class LifecycleState:
    app_id: str
    state: str
    installed: bool
    running: bool
    healthy: bool | None = None
    version: str | None = None
    update_available: bool | None = None
    detail: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass(frozen=True)
class LifecyclePlan:
    app_id: str
    action: str
    current_state: str
    allowed: bool
    reason: str
    requires_confirmation: bool
    confirmation_token: str | None
    target_state: str | None
    write_operation: bool = True

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
