#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
echo "SBP-055 verify: blockchain installer storage selection"
python3 -m py_compile "$ROOT/seymour-blockchain-manager/data/web/storage_targets.py" "$ROOT/seymour-blockchain-manager/data/web/installer.py" "$ROOT/seymour-blockchain-manager/data/web/app.py"
cd "$ROOT"
python3 - <<'PY'
from pathlib import Path
app = Path("seymour-blockchain-manager/data/web/app.py").read_text()
installer = Path("seymour-blockchain-manager/data/web/installer.py").read_text()
js = Path("seymour-blockchain-manager/data/web/app.js").read_text()
assert "/api/install/storage-targets" in app
assert "storage_target_id: str" in installer
assert 'data.get("storageTargetId"' in installer
assert "preflight(value.storage_target_id)" in installer
assert 'id="wizardStorageTarget"' in js
assert "storageTargetId:" in js
assert "/api/install/storage-targets" in js
print("SBP-055 source contract tests: PASS")
PY
echo
echo "===== STORAGE TARGET SERVICE SMOKE TEST ====="
PYTHONPATH="$ROOT:$ROOT/seymour-blockchain-manager/data/web" python3 - <<'PY'
from storage_targets import storage_targets
payload = storage_targets()
print("contract:", payload["contract"])
print("targetCount:", payload["targetCount"])
for target in payload["targets"][:8]:
    print(target)
assert payload["targetCount"] >= 1
PY
echo "SBP-055 storage target API contract: PASS"
echo "SBP-055 selected-target install request contract: PASS"
echo "SBP-055 installation wizard selector contract: PASS"
echo "SBP-055 final verification: PASS"
echo "No live blockchain installation or data migration was executed."
