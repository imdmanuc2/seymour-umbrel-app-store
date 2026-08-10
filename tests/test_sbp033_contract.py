#!/usr/bin/env python3
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
contract = json.loads((root / "shared/contracts/app-lifecycle-audit-v1.json").read_text())

assert contract["contract"] == "seymour.lifecycle-audit-record"
assert contract["version"] == "1.0"
assert contract["storage"] == "append-only-jsonl"
assert contract["bestEffort"] is True
assert contract["executionOutcomeIndependent"] is True
assert contract["directDockerLifecycle"] is False
assert contract["repositoryRuntimeData"] is False
assert contract["pathEnvironmentVariable"] == "SEYMOUR_LIFECYCLE_AUDIT_PATH"

print("SBP-033 lifecycle audit contract verification: PASS")
