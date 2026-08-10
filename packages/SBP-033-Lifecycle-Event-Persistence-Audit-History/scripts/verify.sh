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
python3 tests/test_sbp033_audit.py
python3 tests/test_sbp033_contract.py

python3 -m py_compile \
  shared/app_lifecycle/model.py \
  shared/app_lifecycle/engine.py \
  shared/app_lifecycle/executor.py \
  shared/app_lifecycle/projection.py \
  shared/app_lifecycle/audit.py

python3 - <<'PY'
from pathlib import Path
import tempfile
from shared.app_lifecycle import (
    LifecycleAuditRecorder,
    LifecycleAuditStore,
    LifecycleExecutionResult,
    LifecycleResultProjector,
)

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
    correlation_id="sbp-033-verify",
    observed_at="2026-08-10T00:00:00Z",
)
with tempfile.TemporaryDirectory(prefix="sbp033-verify-") as tmp:
    store = LifecycleAuditStore(Path(tmp) / "audit-events.jsonl")
    persisted = LifecycleAuditRecorder(store).record(projection.event)
    history = store.history(correlation_id="sbp-033-verify")
    print("\n===== AUDIT WRITE RESULT =====")
    print(persisted.as_dict())
    print("\n===== AUDIT HISTORY =====")
    print([record.as_dict() for record in history])
    assert persisted.persisted is True
    assert len(history) == 1
    assert history[0].event["correlation_id"] == "sbp-033-verify"
PY

echo
echo "SBP-033 append-only audit persistence verification: PASS"
echo "SBP-033 audit history/filter verification: PASS"
echo "SBP-033 malformed-record tolerance verification: PASS"
echo "SBP-033 best-effort persistence boundary verification: PASS"
echo "SBP-033 direct Docker lifecycle prohibition: PASS"
echo "SBP-033 final verification: PASS"
echo "No live Umbrel lifecycle write action was executed by verify.sh."
echo "verify.sh wrote audit data only inside temporary directories."
