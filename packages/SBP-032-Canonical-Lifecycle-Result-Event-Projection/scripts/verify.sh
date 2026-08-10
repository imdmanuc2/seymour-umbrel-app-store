#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
cd "$ROOT"

python3 tests/test_sbp030_lifecycle_model.py
python3 tests/test_sbp030_contract.py
python3 tests/test_sbp031_executor.py
python3 tests/test_sbp031_contract.py
python3 tests/test_sbp032_projection.py
python3 tests/test_sbp032_contract.py

python3 -m py_compile \
  shared/app_lifecycle/model.py \
  shared/app_lifecycle/engine.py \
  shared/app_lifecycle/executor.py \
  shared/app_lifecycle/projection.py

python3 - <<'PY'
from shared.app_lifecycle import LifecycleExecutionResult, LifecycleResultProjector
execution = LifecycleExecutionResult(
    app_id="seymour-bch-node",
    action="restart",
    allowed=True,
    executed=True,
    success=True,
    reason="restart completed through fake native Umbrel lifecycle bridge.",
    confirmation_token="RESTART-seymour-bch-node",
    before={"state": "running"},
    after={"state": "running"},
    native_operation={"success": True, "fake": True},
    error=None,
)
projection = LifecycleResultProjector().project(
    execution,
    correlation_id="sbp-032-verify",
    observed_at="2026-08-10T00:00:00Z",
)
print("\n===== CANONICAL RESULT =====")
print(projection.result.as_dict())
print("\n===== CANONICAL EVENT =====")
print(projection.event.as_dict())
assert projection.result.correlation_id == projection.event.correlation_id
assert projection.result.lifecycle_state == "running"
assert projection.event.event_type == "lifecycle.action.succeeded"
PY

echo
echo "SBP-032 result/event correlation verification: PASS"
echo "SBP-032 opaque native evidence verification: PASS"
echo "SBP-032 direct Docker lifecycle prohibition: PASS"
echo "SBP-032 persistence boundary verification: PASS"
echo "SBP-032 final verification: PASS"
echo "No live Umbrel lifecycle write action was executed by verify.sh."
