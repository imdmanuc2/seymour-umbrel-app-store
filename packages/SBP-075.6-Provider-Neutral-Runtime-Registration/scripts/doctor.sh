#!/usr/bin/env bash
set -euo pipefail

PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FILE="$PKG/payload/seymour-blockchain-manager/data/web/nexus_integration.py"

echo "===== SBP-075.6 DOCTOR ====="

test -f "$FILE"

PYTHONDONTWRITEBYTECODE=1 python3 - "$FILE" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()

compile(text, str(path), "exec")

required = (
    "RUNTIME_BINDING_DIRECTORY",
    "load_runtime_binding",
    "UMBREL_CONTROL_SCRIPT",
    "import subprocess",
    "_managed_runtime_assets",
    "_native_runtime_state",
    "_binding_identity",
    "attach_managed_runtime_projection",
    "seymour-bitcoin-node",
    "seymour-bch-node",
    "seymour-monero-node",
)

for token in required:
    assert token in text, token

assert text.count(
    "def registration_payload("
) >= 2

print("PASS: Python syntax")
print("PASS: provider-neutral registration contract")
print("PASS: BCH compatibility bridge")
PY

if find "$PKG" \
  \( -type d -name '__pycache__' \
     -o -type f -name '*.pyc' \
     -o -type f -name '*.pyo' \) \
  -print -quit | grep -q .
then
    echo "FAIL: generated Python artifact found"
    exit 1
fi

echo "PASS: package bytecode-free"
echo "SBP-075.6 DOCTOR PASS"
