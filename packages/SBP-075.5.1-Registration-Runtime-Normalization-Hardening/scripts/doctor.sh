#!/usr/bin/env bash
set -euo pipefail

PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FILE="$PKG/payload/seymour-blockchain-manager/data/web/nexus_integration.py"

echo "===== SBP-075.5.1 DOCTOR ====="

test -f "$FILE"

PYTHONDONTWRITEBYTECODE=1 python3 - "$FILE" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()

compile(text, str(path), "exec")

required = (
    'runtime.get("container") or {}',
    'runtime.get("rpc") or {}',
    'runtime.get("lifecycleStatus", "unknown")',
    'bool(runtime.get("installed"))',
    'bool(runtime.get("running"))',
)

for token in required:
    assert token in text, token

print("PASS: Python syntax")
print("PASS: defensive runtime normalization contract")
PY

if find "$PKG" \
  \( -type d -name '__pycache__' -o -type f -name '*.pyc' -o -type f -name '*.pyo' \) \
  -print -quit | grep -q .
then
    echo "FAIL: generated Python artifact found"
    exit 1
fi

echo "PASS: package bytecode-free"
echo "SBP-075.5.1 DOCTOR PASS"
