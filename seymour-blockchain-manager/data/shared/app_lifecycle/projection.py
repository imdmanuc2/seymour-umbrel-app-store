from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .executor import LifecycleExecutionResult


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _mapping(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if hasattr(value, "as_dict"):
        value = value.as_dict()
    if isinstance(value, dict):
        return value
    raise TypeError("Lifecycle result must be a mapping or expose as_dict().")


def _state_name(value: Any) -> str | None:
    if not isinstance(value, dict):
        return None
    state = value.get("state")
    return str(state) if state is not None else None


def _event_classification(*, allowed: bool, executed: bool, success: bool | None) -> tuple[str, str]:
    if not allowed:
        return "lifecycle.action.rejected", "warning"
    if not executed:
        if success is False:
            return "lifecycle.action.blocked", "warning"
        return "lifecycle.action.planned", "info"
    if success:
        return "lifecycle.action.succeeded", "info"
    return "lifecycle.action.failed", "error"


@dataclass(frozen=True)
class CanonicalLifecycleResult:
    contract: str
    version: str
    correlation_id: str
    observed_at: str
    app_id: str
    action: str
    allowed: bool
    executed: bool
    success: bool | None
    before_state: str | None
    after_state: str | None
    lifecycle_state: str | None
    reason: str
    error: str | None
    confirmation_required: bool
    confirmation_token: str | None
    evidence: dict[str, Any] | None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CanonicalLifecycleEvent:
    contract: str
    version: str
    correlation_id: str
    observed_at: str
    event_type: str
    severity: str
    source: str
    app_id: str
    action: str
    lifecycle_state: str | None
    success: bool | None
    message: str
    error: str | None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LifecycleProjection:
    result: CanonicalLifecycleResult
    event: CanonicalLifecycleEvent

    def as_dict(self) -> dict[str, Any]:
        return {
            "result": self.result.as_dict(),
            "event": self.event.as_dict(),
        }


class LifecycleResultProjector:
    """Project SBP-031 lifecycle execution results into stable platform contracts."""

    RESULT_CONTRACT = "seymour.lifecycle-result"
    EVENT_CONTRACT = "seymour.lifecycle-event"
    VERSION = "1.0"
    SOURCE = "seymour-app-lifecycle"

    def project(
        self,
        execution: LifecycleExecutionResult | dict[str, Any],
        *,
        correlation_id: str | None = None,
        observed_at: str | None = None,
    ) -> LifecycleProjection:
        data = _mapping(execution)
        cid = correlation_id or str(uuid4())
        timestamp = observed_at or _utc_now()

        before = data.get("before") if isinstance(data.get("before"), dict) else {}
        after = data.get("after") if isinstance(data.get("after"), dict) else {}
        before_state = _state_name(before)
        after_state = _state_name(after)
        lifecycle_state = after_state or before_state

        allowed = bool(data.get("allowed"))
        executed = bool(data.get("executed"))
        success_value = data.get("success")
        success = success_value if isinstance(success_value, bool) else None
        event_type, severity = _event_classification(
            allowed=allowed,
            executed=executed,
            success=success,
        )

        app_id = str(data.get("app_id") or "")
        action = str(data.get("action") or "")
        reason = str(data.get("reason") or "")
        error_value = data.get("error")
        error = str(error_value) if error_value else None
        confirmation_value = data.get("confirmation_token")
        confirmation_token = str(confirmation_value) if confirmation_value else None
        confirmation_required = bool(confirmation_token)
        native_operation = data.get("native_operation")
        evidence = native_operation if isinstance(native_operation, dict) else None

        if not app_id:
            raise ValueError("Lifecycle result is missing app_id.")
        if not action:
            raise ValueError("Lifecycle result is missing action.")

        result = CanonicalLifecycleResult(
            contract=self.RESULT_CONTRACT,
            version=self.VERSION,
            correlation_id=cid,
            observed_at=timestamp,
            app_id=app_id,
            action=action,
            allowed=allowed,
            executed=executed,
            success=success,
            before_state=before_state,
            after_state=after_state,
            lifecycle_state=lifecycle_state,
            reason=reason,
            error=error,
            confirmation_required=confirmation_required,
            confirmation_token=confirmation_token,
            evidence=evidence,
        )

        message = reason or f"Lifecycle action {action} for {app_id}."
        event = CanonicalLifecycleEvent(
            contract=self.EVENT_CONTRACT,
            version=self.VERSION,
            correlation_id=cid,
            observed_at=timestamp,
            event_type=event_type,
            severity=severity,
            source=self.SOURCE,
            app_id=app_id,
            action=action,
            lifecycle_state=lifecycle_state,
            success=success,
            message=message,
            error=error,
        )
        return LifecycleProjection(result=result, event=event)
