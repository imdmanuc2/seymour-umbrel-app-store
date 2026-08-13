from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .operations import LifecycleOperationService


API_CONTRACT = "seymour.lifecycle-api-response"
API_HISTORY_CONTRACT = "seymour.lifecycle-api-history"
API_VERSION = "1.0"


def _bool(value: Any, default: bool = False) -> bool:
    return value if isinstance(value, bool) else default


def _int(value: Any, default: int = 100) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(1, min(parsed, 500))


@dataclass(frozen=True)
class LifecycleApiRequest:
    app_id: str
    action: str
    execute: bool = False
    confirmation: str | None = None
    correlation_id: str | None = None

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "LifecycleApiRequest":
        app_id = str(payload.get("appId") or payload.get("app_id") or "").strip()
        action = str(payload.get("action") or "").strip().lower()
        if not app_id:
            raise ValueError("appId is required.")
        if not action:
            raise ValueError("action is required.")
        confirmation = payload.get("confirmation")
        correlation_id = payload.get("correlationId") or payload.get("correlation_id")
        return cls(
            app_id=app_id,
            action=action,
            execute=_bool(payload.get("execute"), False),
            confirmation=str(confirmation) if confirmation else None,
            correlation_id=str(correlation_id) if correlation_id else None,
        )


class LifecycleApiFacade:
    """Frontend/API adapter over the canonical SBP-034 Operations service.

    This class owns no lifecycle execution logic. It converts HTTP/frontend-style
    camelCase requests into LifecycleOperationService calls and projects the
    canonical response into a stable frontend-safe envelope.
    """

    def __init__(self, service: LifecycleOperationService) -> None:
        self.service = service

    def operation(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        request = LifecycleApiRequest.from_dict(payload)
        response = self.service.request(
            request.app_id,
            request.action,
            execute=request.execute,
            confirmation=request.confirmation,
            correlation_id=request.correlation_id,
        ).as_dict()
        result = response["result"]
        event = response["event"]
        audit = response["audit"]

        return {
            "contract": API_CONTRACT,
            "version": API_VERSION,
            "correlationId": result.get("correlation_id"),
            "appId": result.get("app_id"),
            "action": result.get("action"),
            "allowed": result.get("allowed"),
            "executed": result.get("executed"),
            "success": result.get("success"),
            "beforeState": result.get("before_state"),
            "afterState": result.get("after_state"),
            "lifecycleState": result.get("lifecycle_state"),
            "reason": result.get("reason"),
            "error": result.get("error"),
            "confirmationRequired": result.get("confirmation_required"),
            "confirmationToken": result.get("confirmation_token"),
            "eventType": event.get("event_type"),
            "severity": event.get("severity"),
            "observedAt": event.get("observed_at"),
            "auditPersisted": audit.get("persisted"),
            "auditId": audit.get("audit_id"),
        }

    def history(self, query: Mapping[str, Any]) -> dict[str, Any]:
        app_id = query.get("appId") or query.get("app_id")
        action = query.get("action")
        event_type = query.get("eventType") or query.get("event_type")
        correlation_id = query.get("correlationId") or query.get("correlation_id")
        limit = _int(query.get("limit"), 100)

        records = self.service.history(
            app_id=str(app_id) if app_id else None,
            action=str(action) if action else None,
            event_type=str(event_type) if event_type else None,
            correlation_id=str(correlation_id) if correlation_id else None,
            limit=limit,
        )
        items: list[dict[str, Any]] = []
        for record in records:
            event = record.get("event", {})
            items.append({
                "auditId": record.get("audit_id"),
                "recordedAt": record.get("recorded_at"),
                "correlationId": event.get("correlation_id"),
                "appId": event.get("app_id"),
                "action": event.get("action"),
                "eventType": event.get("event_type"),
                "severity": event.get("severity"),
                "lifecycleState": event.get("lifecycle_state"),
                "success": event.get("success"),
                "message": event.get("message"),
                "error": event.get("error"),
                "observedAt": event.get("observed_at"),
            })

        return {
            "contract": API_HISTORY_CONTRACT,
            "version": API_VERSION,
            "count": len(items),
            "items": items,
        }

    @staticmethod
    def http_status(payload: Mapping[str, Any]) -> int:
        """Map the stable API envelope to an HTTP status without hiding payload detail."""
        if payload.get("contract") != API_CONTRACT:
            return 200
        if payload.get("allowed") is False:
            return 409
        if payload.get("executed") is True and payload.get("success") is False:
            return 502
        if payload.get("success") is False:
            return 400
        return 200
