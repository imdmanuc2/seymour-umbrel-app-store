import json
from pathlib import Path

repo = Path(__file__).resolve().parents[1]
payload = json.loads((repo / "shared/contracts/app-lifecycle-execution-v1.json").read_text())

assert payload["contract"] == "seymour.app-lifecycle-execution"
assert payload["version"] == "1.0"
assert payload["nativeUmbrelLifecycleRequired"] is True
assert payload["directDockerLifecycle"] is False
assert payload["writeOperationsRequireExecuteFlag"] is True
assert payload["writeOperationsRequireConfirmation"] is True
assert payload["preActionStateRead"] is True
assert payload["postActionStateRead"] is True

for field in ["before", "after", "native_operation", "success", "error"]:
    assert field in payload["resultFields"]

print("SBP-031 lifecycle execution contract verification: PASS")
