#!/usr/bin/env python3
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
result = json.loads((root / "shared/contracts/app-lifecycle-result-v1.json").read_text())
event = json.loads((root / "shared/contracts/app-lifecycle-event-v1.json").read_text())

assert result["contract"] == "seymour.lifecycle-result"
assert result["version"] == "1.0"
assert result["nativeEvidenceOpaque"] is True
assert result["directDockerLifecycle"] is False
for field in ("correlation_id", "app_id", "action", "lifecycle_state", "success", "evidence"):
    assert field in result["fields"]

assert event["contract"] == "seymour.lifecycle-event"
assert event["version"] == "1.0"
assert event["persistenceRequired"] is False
assert event["directDockerLifecycle"] is False
assert "lifecycle.action.succeeded" in event["eventTypes"]
assert "lifecycle.action.failed" in event["eventTypes"]

print("SBP-032 lifecycle contracts verification: PASS")
