#!/usr/bin/env python3
from pathlib import Path
import sys
import tempfile

repo = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo))

from shared.app_lifecycle import (
    AppLifecycleEngine,
    LifecycleAuditRecorder,
    LifecycleAuditStore,
    LifecycleExecutor,
    LifecycleOperationService,
)


class FakeOperation:
    def __init__(self, success=True, result=None, error=None):
        self.success = success
        self.result = result or {}
        self.error = error

    def to_dict(self):
        return {"success": self.success, "result": self.result, "error": self.error, "fake": True}


class FakeBridge:
    def __init__(self):
        self.running = True
        self.write_calls = []

    def execute(self, action, app_id, execute=False, confirmation=None):
        if action == "state":
            return FakeOperation(True, {"state": "running" if self.running else "stopped", "installed": True, "running": self.running, "healthy": True})
        self.write_calls.append((action, app_id, execute, confirmation))
        if action == "stop":
            self.running = False
        elif action in {"start", "restart"}:
            self.running = True
        return FakeOperation(True, {"action": action, "appId": app_id})


with tempfile.TemporaryDirectory(prefix="sbp034-") as tmp:
    bridge = FakeBridge()
    executor = LifecycleExecutor(bridge, AppLifecycleEngine())
    store = LifecycleAuditStore(Path(tmp) / "audit.jsonl")
    service = LifecycleOperationService(executor, audit_recorder=LifecycleAuditRecorder(store))

    planned = service.request(
        "seymour-bch-node",
        "restart",
        correlation_id="corr-plan",
        observed_at="2026-08-10T00:00:00Z",
    )
    assert planned.contract == "seymour.lifecycle-operation-response"
    assert planned.result["executed"] is False
    assert planned.event["event_type"] == "lifecycle.action.planned"
    assert planned.audit["persisted"] is True
    assert bridge.write_calls == []

    executed = service.request(
        "seymour-bch-node",
        "restart",
        execute=True,
        confirmation="RESTART-seymour-bch-node",
        correlation_id="corr-exec",
        observed_at="2026-08-10T00:00:01Z",
    )
    assert executed.result["executed"] is True
    assert executed.result["success"] is True
    assert executed.event["event_type"] == "lifecycle.action.succeeded"
    assert executed.audit["persisted"] is True
    assert len(bridge.write_calls) == 1
    assert executed.result["correlation_id"] == executed.event["correlation_id"] == "corr-exec"

    history = service.history(correlation_id="corr-exec")
    assert len(history) == 1
    assert history[0]["event"]["action"] == "restart"

print("SBP-034 lifecycle operations integration verification: PASS")
