from pathlib import Path
import sys
repo = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo))
from shared.app_lifecycle import AppLifecycleEngine

engine = AppLifecycleEngine()

running = engine.normalize_state(
    app_id="example-app",
    installed=True,
    running=True,
    native_state="ready",
    healthy=True,
)
assert running.state == "running"
assert engine.capabilities(running)["restart"] is True
assert engine.capabilities(running)["install"] is False

plan = engine.plan(running, "restart")
assert plan.allowed is True
assert plan.confirmation_token == "RESTART-example-app"
assert plan.target_state == "restarting"

missing = engine.normalize_state(
    app_id="example-app",
    installed=False,
    running=False,
    native_state="ready",
)
assert missing.state == "not-installed"
assert engine.plan(missing, "install").allowed is True

degraded = engine.normalize_state(
    app_id="example-app",
    installed=True,
    running=True,
    native_state="running",
    healthy=False,
)
assert degraded.state == "degraded"
assert engine.plan(degraded, "restart").allowed is True

print("SBP-030 lifecycle state/action model verification: PASS")
