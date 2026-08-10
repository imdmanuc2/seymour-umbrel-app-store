from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .audit import LifecycleAuditRecorder, LifecycleAuditStore, LifecycleAuditWriteResult
from .executor import LifecycleExecutor
from .projection import LifecycleProjection, LifecycleResultProjector


@dataclass(frozen=True)
class LifecycleOperationResponse:
    """Operations-facing response for one canonical lifecycle request."""

    contract: str
    version: str
    result: dict[str, Any]
    event: dict[str, Any]
    audit: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class LifecycleOperationService:
    """Compose the canonical lifecycle chain without introducing another executor.

    Execution remains owned by SBP-031 LifecycleExecutor. SBP-034 only orchestrates
    executor -> SBP-032 projection -> SBP-033 best-effort audit persistence for
    Operations/API consumers.
    """

    CONTRACT = "seymour.lifecycle-operation-response"
    VERSION = "1.0"

    def __init__(
        self,
        executor: LifecycleExecutor,
        *,
        projector: LifecycleResultProjector | None = None,
        audit_recorder: LifecycleAuditRecorder | None = None,
    ) -> None:
        self.executor = executor
        self.projector = projector or LifecycleResultProjector()
        self.audit_recorder = audit_recorder or LifecycleAuditRecorder()

    def request(
        self,
        app_id: str,
        action: str,
        *,
        execute: bool = False,
        confirmation: str | None = None,
        correlation_id: str | None = None,
        observed_at: str | None = None,
    ) -> LifecycleOperationResponse:
        execution = self.executor.execute(
            app_id,
            action,
            execute=execute,
            confirmation=confirmation,
        )
        projection: LifecycleProjection = self.projector.project(
            execution,
            correlation_id=correlation_id,
            observed_at=observed_at,
        )
        audit: LifecycleAuditWriteResult = self.audit_recorder.record(projection.event)
        return LifecycleOperationResponse(
            contract=self.CONTRACT,
            version=self.VERSION,
            result=projection.result.as_dict(),
            event=projection.event.as_dict(),
            audit=audit.as_dict(),
        )

    def history(
        self,
        *,
        app_id: str | None = None,
        action: str | None = None,
        event_type: str | None = None,
        correlation_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        store = getattr(self.audit_recorder, "store", None)
        if not isinstance(store, LifecycleAuditStore):
            return []
        return [
            record.as_dict()
            for record in store.history(
                app_id=app_id,
                action=action,
                event_type=event_type,
                correlation_id=correlation_id,
                limit=limit,
            )
        ]
