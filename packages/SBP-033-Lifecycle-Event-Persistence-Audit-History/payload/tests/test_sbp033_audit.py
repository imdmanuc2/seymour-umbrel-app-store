#!/usr/bin/env python3
from pathlib import Path
import os
import stat
import sys
import tempfile

repo = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo))

from shared.app_lifecycle import LifecycleAuditRecorder, LifecycleAuditStore, LifecycleResultProjector
from shared.app_lifecycle import LifecycleExecutionResult


def event_for(action: str, correlation: str, *, success: bool = True):
    execution = LifecycleExecutionResult(
        app_id="seymour-bch-node",
        action=action,
        allowed=True,
        executed=True,
        success=success,
        reason=f"{action} completed through fake native Umbrel lifecycle bridge.",
        confirmation_token=f"{action.upper()}-seymour-bch-node",
        before={"state": "running"},
        after={"state": "running" if success else "degraded"},
        native_operation={"success": success, "fake": True},
        error=None if success else "fake failure",
    )
    return LifecycleResultProjector().project(
        execution,
        correlation_id=correlation,
        observed_at="2026-08-10T00:00:00Z",
    ).event


with tempfile.TemporaryDirectory(prefix="sbp033-") as tmp:
    path = Path(tmp) / "audit" / "events.jsonl"
    store = LifecycleAuditStore(path)
    first = store.append(event_for("restart", "corr-1"), audit_id="audit-1", recorded_at="2026-08-10T00:00:01Z")
    second = store.append(event_for("stop", "corr-2"), audit_id="audit-2", recorded_at="2026-08-10T00:00:02Z")

    assert first.audit_id == "audit-1"
    assert second.audit_id == "audit-2"
    assert path.exists()
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert len(path.read_text().splitlines()) == 2

    all_history = store.history(limit=10)
    assert [record.audit_id for record in all_history] == ["audit-2", "audit-1"]
    assert store.history(action="restart")[0].audit_id == "audit-1"
    assert store.history(correlation_id="corr-2")[0].event["action"] == "stop"
    assert store.history(event_type="lifecycle.action.succeeded")
    assert store.history(app_id="does-not-exist") == []

    # A corrupt line must not destroy readable audit history.
    with path.open("a", encoding="utf-8") as handle:
        handle.write("{not-json}\n")
    assert len(store.history(limit=10)) == 2

    # Best-effort recorder reports persistence failure instead of raising.
    blocker = Path(tmp) / "blocker"
    blocker.write_text("file")
    failing = LifecycleAuditRecorder(LifecycleAuditStore(blocker / "events.jsonl"))
    result = failing.record(event_for("restart", "corr-3"))
    assert result.persisted is False
    assert result.error

print("SBP-033 lifecycle audit persistence/history verification: PASS")
