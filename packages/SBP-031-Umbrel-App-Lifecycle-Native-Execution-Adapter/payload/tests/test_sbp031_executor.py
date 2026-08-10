from dataclasses import dataclass
from pathlib import Path
import sys

repo = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo))

from shared.app_lifecycle import LifecycleExecutor


@dataclass
class FakeOperation:
    action: str
    app_id: str
    executed: bool
    success: bool | None
    result: object
    error: str | None = None

    def to_dict(self):
        return {
            "action": self.action,
            "app_id": self.app_id,
            "executed": self.executed,
            "success": self.success,
            "result": self.result,
            "error": self.error,
        }


class FakeBridge:
    def __init__(self):
        self.state = "running"
        self.write_calls = []

    def execute(self, action, app_id, *, execute=False, confirmation=None):
        if action == "state":
            return FakeOperation(action, app_id, True, True, {"state": self.state, "installed": True})
        self.write_calls.append((action, app_id, execute, confirmation))
        if action == "restart":
            self.state = "running"
        elif action == "stop":
            self.state = "stopped"
        elif action == "start":
            self.state = "running"
        return FakeOperation(action, app_id, True, True, {"state": self.state})


bridge = FakeBridge()
executor = LifecycleExecutor(bridge)

planned = executor.execute("seymour-bch-node", "restart")
assert planned.allowed is True
assert planned.executed is False
assert planned.confirmation_token == "RESTART-seymour-bch-node"
assert bridge.write_calls == []

bad = executor.execute(
    "seymour-bch-node",
    "restart",
    execute=True,
    confirmation="WRONG",
)
assert bad.success is False
assert bad.executed is False
assert bridge.write_calls == []

result = executor.execute(
    "seymour-bch-node",
    "restart",
    execute=True,
    confirmation="RESTART-seymour-bch-node",
)
assert result.success is True
assert result.executed is True
assert result.before["state"] == "running"
assert result.after["state"] == "running"
assert bridge.write_calls[-1] == (
    "restart",
    "seymour-bch-node",
    True,
    "RESTART-seymour-bch-node",
)

bridge.state = "stopped"
blocked = executor.execute("seymour-bch-node", "restart")
assert blocked.allowed is False
assert blocked.executed is False

print("SBP-031 lifecycle native execution adapter verification: PASS")
