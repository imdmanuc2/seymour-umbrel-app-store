from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any, Iterable, Mapping
from uuid import uuid4

try:
    import fcntl
except ImportError:  # pragma: no cover - Linux/Umbrel provides fcntl.
    fcntl = None

AUDIT_CONTRACT = "seymour.lifecycle-audit-record"
AUDIT_VERSION = "1.0"
AUDIT_ENV = "SEYMOUR_LIFECYCLE_AUDIT_PATH"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def default_audit_path() -> Path:
    configured = os.environ.get(AUDIT_ENV)
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".seymour" / "lifecycle" / "audit-events.jsonl"


def _event_mapping(event: Any) -> dict[str, Any]:
    if hasattr(event, "as_dict"):
        event = event.as_dict()
    if isinstance(event, Mapping):
        return dict(event)
    raise TypeError("Lifecycle audit event must be a mapping or expose as_dict().")


@dataclass(frozen=True)
class LifecycleAuditRecord:
    contract: str
    version: str
    audit_id: str
    recorded_at: str
    event: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LifecycleAuditWriteResult:
    persisted: bool
    audit_id: str | None
    path: str
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class LifecycleAuditStore:
    """Append-only local audit store for canonical SBP-032 lifecycle events."""

    def __init__(self, path: str | os.PathLike[str] | None = None) -> None:
        self.path = Path(path).expanduser() if path is not None else default_audit_path()

    def append(
        self,
        event: Any,
        *,
        audit_id: str | None = None,
        recorded_at: str | None = None,
    ) -> LifecycleAuditRecord:
        event_dict = _event_mapping(event)
        if event_dict.get("contract") != "seymour.lifecycle-event":
            raise ValueError("SBP-033 accepts canonical seymour.lifecycle-event payloads only.")
        if event_dict.get("version") != "1.0":
            raise ValueError("Unsupported lifecycle event contract version.")

        record = LifecycleAuditRecord(
            contract=AUDIT_CONTRACT,
            version=AUDIT_VERSION,
            audit_id=audit_id or str(uuid4()),
            recorded_at=recorded_at or _utc_now(),
            event=event_dict,
        )
        payload = (json.dumps(record.as_dict(), separators=(",", ":"), sort_keys=True) + "\n").encode("utf-8")

        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd = os.open(self.path, os.O_CREAT | os.O_APPEND | os.O_WRONLY, 0o600)
        try:
            if fcntl is not None:
                fcntl.flock(fd, fcntl.LOCK_EX)
            os.write(fd, payload)
            os.fsync(fd)
        finally:
            if fcntl is not None:
                try:
                    fcntl.flock(fd, fcntl.LOCK_UN)
                except OSError:
                    pass
            os.close(fd)

        try:
            os.chmod(self.path, 0o600)
        except OSError:
            pass
        return record

    def history(
        self,
        *,
        app_id: str | None = None,
        action: str | None = None,
        event_type: str | None = None,
        correlation_id: str | None = None,
        limit: int = 100,
        newest_first: bool = True,
    ) -> list[LifecycleAuditRecord]:
        if limit < 1:
            return []
        if not self.path.exists():
            return []

        records: list[LifecycleAuditRecord] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    raw = json.loads(line)
                    if raw.get("contract") != AUDIT_CONTRACT or raw.get("version") != AUDIT_VERSION:
                        continue
                    event = raw.get("event")
                    if not isinstance(event, dict):
                        continue
                    record = LifecycleAuditRecord(
                        contract=raw["contract"],
                        version=raw["version"],
                        audit_id=str(raw["audit_id"]),
                        recorded_at=str(raw["recorded_at"]),
                        event=event,
                    )
                except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                    continue

                if app_id is not None and event.get("app_id") != app_id:
                    continue
                if action is not None and event.get("action") != action:
                    continue
                if event_type is not None and event.get("event_type") != event_type:
                    continue
                if correlation_id is not None and event.get("correlation_id") != correlation_id:
                    continue
                records.append(record)

        if newest_first:
            records.reverse()
        return records[:limit]


class LifecycleAuditRecorder:
    """Best-effort adapter that keeps audit failures separate from action results."""

    def __init__(self, store: LifecycleAuditStore | None = None) -> None:
        self.store = store or LifecycleAuditStore()

    def record(self, event: Any) -> LifecycleAuditWriteResult:
        try:
            record = self.store.append(event)
            return LifecycleAuditWriteResult(
                persisted=True,
                audit_id=record.audit_id,
                path=str(self.store.path),
                error=None,
            )
        except Exception as exc:  # Persistence must never redefine lifecycle success.
            return LifecycleAuditWriteResult(
                persisted=False,
                audit_id=None,
                path=str(self.store.path),
                error=str(exc),
            )
