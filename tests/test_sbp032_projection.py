#!/usr/bin/env python3
from pathlib import Path
import sys

repo = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo))

from shared.app_lifecycle import LifecycleExecutionResult, LifecycleResultProjector

projector = LifecycleResultProjector()

success = LifecycleExecutionResult(
    app_id="seymour-bch-node",
    action="restart",
    allowed=True,
    executed=True,
    success=True,
    reason="restart completed through the native Umbrel lifecycle bridge.",
    confirmation_token="RESTART-seymour-bch-node",
    before={"state": "running"},
    after={"state": "running"},
    native_operation={"success": True, "operation": "restart"},
    error=None,
)
projection = projector.project(success, correlation_id="test-correlation", observed_at="2026-08-10T00:00:00Z")
assert projection.result.contract == "seymour.lifecycle-result"
assert projection.event.contract == "seymour.lifecycle-event"
assert projection.result.correlation_id == projection.event.correlation_id == "test-correlation"
assert projection.result.lifecycle_state == "running"
assert projection.result.evidence == {"success": True, "operation": "restart"}
assert projection.event.event_type == "lifecycle.action.succeeded"
assert projection.event.severity == "info"

planned = LifecycleExecutionResult(
    app_id="seymour-bch-node",
    action="stop",
    allowed=True,
    executed=False,
    success=None,
    reason="stop is allowed while seymour-bch-node is running.",
    confirmation_token="STOP-seymour-bch-node",
    before={"state": "running"},
    after=None,
    native_operation=None,
    error=None,
)
planned_projection = projector.project(planned)
assert planned_projection.event.event_type == "lifecycle.action.planned"
assert planned_projection.result.lifecycle_state == "running"
assert planned_projection.result.success is None

blocked = dict(planned.as_dict())
blocked["success"] = False
blocked["reason"] = "Lifecycle write confirmation mismatch."
blocked["error"] = "Expected confirmation token: STOP-seymour-bch-node"
blocked_projection = projector.project(blocked)
assert blocked_projection.event.event_type == "lifecycle.action.blocked"
assert blocked_projection.event.severity == "warning"

rejected = dict(planned.as_dict())
rejected.update({"allowed": False, "success": False, "confirmation_token": None})
rejected_projection = projector.project(rejected)
assert rejected_projection.event.event_type == "lifecycle.action.rejected"

failed = dict(success.as_dict())
failed.update({"success": False, "error": "native failure", "after": {"state": "degraded"}})
failed_projection = projector.project(failed)
assert failed_projection.event.event_type == "lifecycle.action.failed"
assert failed_projection.event.severity == "error"
assert failed_projection.result.lifecycle_state == "degraded"

print("SBP-032 lifecycle projection verification: PASS")
