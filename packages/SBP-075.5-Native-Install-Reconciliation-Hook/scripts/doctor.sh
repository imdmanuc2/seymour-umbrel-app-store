#!/usr/bin/env bash
set -euo pipefail

PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

ROOT_BRIDGE="$PKG/payload/shared/umbrel_control/bridge.py"
ROOT_HTTP="$PKG/payload/shared/umbrel_control/http_client.py"

MANAGER_BRIDGE="$PKG/payload/seymour-blockchain-manager/data/shared/umbrel_control/bridge.py"
MANAGER_HTTP="$PKG/payload/seymour-blockchain-manager/data/shared/umbrel_control/http_client.py"

echo "===== SBP-075.5 DOCTOR ====="

for FILE in \
  "$ROOT_BRIDGE" \
  "$ROOT_HTTP" \
  "$MANAGER_BRIDGE" \
  "$MANAGER_HTTP"
do
  test -f "$FILE"
done

echo "PASS: complete control payload exists"

PYTHONDONTWRITEBYTECODE=1 \
python3 - "$ROOT_BRIDGE" "$ROOT_HTTP" "$MANAGER_BRIDGE" "$MANAGER_HTTP" <<'PY'
from pathlib import Path
import sys

for filename in sys.argv[1:]:
    path = Path(filename)

    compile(
        path.read_text(),
        str(path),
        "exec",
    )

print("PASS: Python syntax")
PY

cmp -s "$ROOT_BRIDGE" "$MANAGER_BRIDGE"
cmp -s "$ROOT_HTTP" "$MANAGER_HTTP"

echo "PASS: package projections identical"

PYTHONDONTWRITEBYTECODE=1 \
python3 - "$ROOT_BRIDGE" <<'PY'
from pathlib import Path
import sys

text = Path(sys.argv[1]).read_text()

required = (
    "UmbrelHttpClient",
    "reconcile_installed_runtime_binding",
    'if action == "install" and app_id is not None:',
    "binding_path.is_file()",
    '"runtimeBindingReconciliation"',
    "post_install_reconciliation_started = False",
    "not post_install_reconciliation_started",
    "self.wait_for_state(",
)

for token in required:
    assert token in text, token

print("PASS: hardened lifecycle reconciliation contract")
PY

if find "$PKG" \
  \( \
    -type d -name '__pycache__' \
    -o -type f -name '*.pyc' \
    -o -type f -name '*.pyo' \
  \) \
  -print -quit \
  | grep -q .
then
    echo "ERROR: generated Python artifacts found"
    exit 1
fi

echo "PASS: package bytecode-free"
echo "SBP-075.5 DOCTOR PASS"
