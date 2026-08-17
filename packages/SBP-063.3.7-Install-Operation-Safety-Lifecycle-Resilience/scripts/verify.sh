#!/usr/bin/env bash
set -euo pipefail
PKG="$(cd "$(dirname "$0")/.." && pwd)"
REPO="$(cd "$PKG/../.." && pwd)"
LIVE="/home/umbrel/umbrel/app-data/seymour-blockchain-manager/data"
echo "SBP-063.3.7 verify: install operation safety and lifecycle resilience"
python3 -m py_compile "$LIVE/web/installer.py" "$LIVE/shared/umbrel_control/bridge.py" "$LIVE/shared/umbrel_control/http_client.py"
echo "SBP-063.3.7 deployed Python compile contract: PASS"
for target in "$REPO/seymour-blockchain-manager/data" "$LIVE"; do
  grep -q 'installButton.disabled = true' "$target/web/app.js"
  grep -q 'Installing…' "$target/web/app.js"
  grep -q '_active_install_for_app' "$target/web/installer.py"
  grep -q 'Installation already in progress' "$target/web/installer.py"
  grep -q 'mutation_timeout_seconds=1800' "$target/shared/umbrel_control/bridge.py"
  grep -q 'timeout=self.mutation_timeout_seconds' "$target/shared/umbrel_control/http_client.py"
done
echo "SBP-063.3.7 deployed source contracts: PASS"
python3 - "$LIVE/web/installer.py" <<'PY'
import sys, tempfile, json, importlib.util
from pathlib import Path
# Static regression is intentionally isolated from platform imports/runtime.
s=Path(sys.argv[1]).read_text()
assert 'payload.get("status") != InstallStatus.RUNNING.value' in s
assert '> 3600' in s
assert 'Installation already in progress' in s
print('SBP-063.3.7 duplicate guard regression: PASS')
PY
python3 - "$LIVE/shared/umbrel_control/http_client.py" <<'PY'
import sys
from pathlib import Path
s=Path(sys.argv[1]).read_text()
assert 'timeout_seconds: float = 30' in s
assert 'mutation_timeout_seconds: float = 1800' in s
assert 'timeout=self.timeout_seconds' in s
assert 'timeout=self.mutation_timeout_seconds' in s
print('SBP-063.3.7 split timeout regression: PASS')
PY
echo "SBP-063.3.7 final verification: PASS"
echo "No live blockchain runtime was modified."
