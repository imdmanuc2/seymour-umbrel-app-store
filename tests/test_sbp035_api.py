#!/usr/bin/env python3
from pathlib import Path
import sys
import tempfile

repo = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo))

from shared.app_lifecycle import (
    AppLifecycleEngine,
    LifecycleApiFacade,
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


with tempfile.TemporaryDirectory(prefix="sbp035-") as tmp:
    bridge = FakeBridge()
    executor = LifecycleExecutor(bridge, AppLifecycleEngine())
    store = LifecycleAuditStore(Path(tmp) / "audit.jsonl")
    service = LifecycleOperationService(executor, audit_recorder=LifecycleAuditRecorder(store))
    api = LifecycleApiFacade(service)

    planned = api.operation({"appId": "seymour-bch-node", "action": "restart"})
    assert planned["contract"] == "seymour.lifecycle-api-response"
    assert planned["allowed"] is True
    assert planned["executed"] is False
    assert planned["confirmationRequired"] is True
    assert planned["confirmationToken"] == "RESTART-seymour-bch-node"
    assert planned["eventType"] == "lifecycle.action.planned"
    assert planned["auditPersisted"] is True
    assert bridge.write_calls == []
    assert api.http_status(planned) == 200

    executed = api.operation({
        "appId": "seymour-bch-node",
        "action": "restart",
        "execute": True,
        "confirmation": planned["confirmationToken"],
        "correlationId": "sbp-035-exec",
    })
    assert executed["executed"] is True
    assert executed["success"] is True
    assert executed["correlationId"] == "sbp-035-exec"
    assert len(bridge.write_calls) == 1
    assert api.http_status(executed) == 200

    history = api.history({"appId": "seymour-bch-node", "limit": 10})
    assert history["contract"] == "seymour.lifecycle-api-history"
    assert history["count"] == 2
    assert all(item["appId"] == "seymour-bch-node" for item in history["items"])

print("SBP-035 lifecycle API/frontend contract verification: PASS")
