#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"

python3 -m py_compile   "$ROOT/shared/app_lifecycle/"*.py   "$ROOT/seymour-blockchain-manager/data/web/lifecycle_routes.py"

PYTHONPATH="$ROOT" python3 - <<'TESTPY'
from shared.app_lifecycle import AppLifecycleEngine, LifecycleExecutor
from shared.app_lifecycle.model import LifecycleState

engine = AppLifecycleEngine()

class NeverNativeBridge:
    def execute(self, *args, **kwargs):
        raise AssertionError("native state path must not be used for canonical provider app")

class FakeProvider:
    def __init__(self, state):
        self.state = state
    def read_state(self, app_id, engine):
        if app_id != "seymour-bch-node":
            return None
        return LifecycleState(
            app_id=app_id,
            state=self.state,
            installed=True,
            running=self.state in {"starting", "syncing", "running", "degraded"},
            healthy=(
                True if self.state == "running"
                else False if self.state in {"degraded", "error"}
                else None
            ),
            detail={"runtimeState": self.state},
        )

cases = {
    "running": ("restart", True),
    "syncing": ("restart", True),
    "stopped": ("start", True),
    "degraded": ("restart", True),
    "offline": ("start", True),
    "error": ("restart", True),
    "unknown": ("restart", False),
}

for state, (action, expected_allowed) in cases.items():
    executor = LifecycleExecutor(
        NeverNativeBridge(),
        engine,
        state_provider=FakeProvider(state),
    )
    result = executor.execute("seymour-bch-node", action, execute=False)
    assert result.before["state"] == state, (state, result.before)
    assert result.allowed is expected_allowed, (state, action, result.as_dict())
    assert result.executed is False

print("SBP-037 canonical runtime state -> lifecycle state verification: PASS")
print("SBP-037 canonical state policy verification: PASS")
TESTPY

PYTHONPATH="$ROOT" python3 - <<'TESTPY'
from shared.app_lifecycle import AppLifecycleEngine, LifecycleExecutor

class NativeBridge:
    def execute(self, action, app_id, **kwargs):
        assert action == "state"
        return {"result": {"state": "ready"}}

class UnsupportedProvider:
    def read_state(self, app_id, engine):
        return None

executor = LifecycleExecutor(
    NativeBridge(),
    AppLifecycleEngine(),
    state_provider=UnsupportedProvider(),
)
state = executor.read_state("seymour-blockchain-manager")
assert state.state == "running", state.as_dict()
print("SBP-037 non-provider native Umbrel fallback verification: PASS")
TESTPY

PYTHONPATH="$ROOT" python3 - <<'TESTPY'
from shared.app_lifecycle.runtime_state import CanonicalRuntimeStateProvider

assert CanonicalRuntimeStateProvider._extract_runtime_state({"runtimeState": "running"}) == "running"
assert CanonicalRuntimeStateProvider._extract_runtime_state({"runtime": {"runtimeState": "syncing"}}) == "syncing"
assert CanonicalRuntimeStateProvider._extract_runtime_state({"status": "online", "healthy": True}) == "unknown"

print("SBP-037 no legacy status inference verification: PASS")
TESTPY

grep -Fq 'CanonicalRuntimeStateProvider'   "$ROOT/seymour-blockchain-manager/data/web/lifecycle_routes.py"
grep -Fq 'state_provider=state_provider'   "$ROOT/seymour-blockchain-manager/data/web/lifecycle_routes.py"

! grep -Eq 'docker[[:space:]].*(start|stop|restart|rm|compose[[:space:]]+(up|down|restart))'   "$ROOT/shared/app_lifecycle/runtime_state.py" || {
  echo "SBP-037 verify: prohibited Docker lifecycle path found"; exit 1;
}

echo "SBP-037 Blockchain Manager reconciliation wiring verification: PASS"
echo "SBP-037 direct Docker lifecycle prohibition: PASS"
echo "SBP-037 final verification: PASS"
echo "No live Umbrel lifecycle write action was executed by verify.sh."
