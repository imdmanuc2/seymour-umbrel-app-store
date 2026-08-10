#!/usr/bin/env python3
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
api = json.loads((root / "shared/contracts/app-lifecycle-api-v1.json").read_text())
result = json.loads((root / "shared/contracts/app-lifecycle-result-v1.json").read_text())
assert api["contract"] == "seymour.lifecycle-api-response"
assert api["version"] == "1.0"
assert api["executionOwner"].startswith("SBP-031 LifecycleExecutor")
assert api["duplicateExecutionPath"] is False
assert api["directDockerLifecycle"] is False
assert api["camelCaseFrontendFields"] is True
assert api["confirmationTokenForwardedFromCanonicalResult"] is True
assert "confirmation_token" in result["fields"]
print("SBP-035 lifecycle API contract verification: PASS")
