#!/usr/bin/env python3
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
contract = json.loads((root / "shared/contracts/app-lifecycle-operation-v1.json").read_text())
assert contract["contract"] == "seymour.lifecycle-operation-response"
assert contract["version"] == "1.0"
assert contract["executionOwner"] == "SBP-031 LifecycleExecutor"
assert contract["duplicateExecutionPath"] is False
assert contract["directDockerLifecycle"] is False
assert contract["auditBestEffort"] is True
assert contract["writeSafety"]["planningDefault"] is True
assert contract["writeSafety"]["confirmationTokenRequiredForWrites"] is True
print("SBP-034 lifecycle operations contract verification: PASS")
