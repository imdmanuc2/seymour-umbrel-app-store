#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PKG="$ROOT/packages/SBP-075.3-Canonical-Runtime-Binding-Materialization"

CANON="$PKG/payload/shared/blockchain_install/runtime_binding_materializer.py"
MANAGER="$PKG/payload/seymour-blockchain-manager/data/shared/blockchain_install/runtime_binding_materializer.py"

echo "===== SBP-075.3 DOCTOR ====="

test -f "$CANON"
test -f "$MANAGER"

echo "PASS: materializer payloads exist"

PYTHONDONTWRITEBYTECODE=1 \
python3 - "$CANON" "$MANAGER" <<'PY'
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

cmp -s "$CANON" "$MANAGER"

echo "PASS: package projections identical"

grep -q \
  'RuntimeBindingMode.SINGLE_PATH' \
  "$CANON"

grep -q \
  'RuntimeBindingMode.HYBRID_BLOCKS' \
  "$CANON"

grep -q \
  'def materialize_runtime_binding' \
  "$CANON"

echo "PASS: canonical materialization contract present"

if find "$PKG" \
  \( \
    -type d -name '__pycache__' \
    -o -type f -name '*.pyc' \
    -o -type f -name '*.pyo' \
  \) \
  -print -quit \
  | grep -q .
then
    echo "ERROR: generated Python bytecode found"
    exit 1
fi

echo "PASS: package bytecode-free"

echo "SBP-075.3 DOCTOR PASS"
