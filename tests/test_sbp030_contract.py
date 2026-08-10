import json
from pathlib import Path

repo = Path(__file__).resolve().parents[1]
payload = json.loads(
    (repo / "shared/contracts/app-lifecycle-v1.json").read_text()
)

assert payload["contract"] == "seymour.app-lifecycle"
assert payload["version"] == "1.0"
assert payload["nativeUmbrelLifecyclePreferred"] is True
assert payload["directDockerLifecycle"] is False
assert payload["writeOperationsRequireConfirmation"] is True

for action in ["install","start","stop","restart","update","uninstall"]:
    assert action in payload["actions"]

print("SBP-030 lifecycle contract verification: PASS")
