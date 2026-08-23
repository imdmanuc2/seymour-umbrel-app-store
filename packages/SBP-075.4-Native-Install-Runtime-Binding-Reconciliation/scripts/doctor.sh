#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PKG="$ROOT/packages/SBP-075.4-Native-Install-Runtime-Binding-Reconciliation"

echo "===== SBP-075.4 DOCTOR ====="

PYTHONDONTWRITEBYTECODE=1 \
python3 - "$ROOT" "$PKG" <<'PY'
from pathlib import Path
import ast
import sys

root = Path(sys.argv[1])
pkg = Path(sys.argv[2])

paths = [
    root / "shared/blockchain_install/runtime_binding.py",
    root / "shared/blockchain_install/runtime_binding_reconciler.py",
    root / "seymour-blockchain-manager/data/shared/blockchain_install/runtime_binding.py",
    root / "seymour-blockchain-manager/data/shared/blockchain_install/runtime_binding_reconciler.py",
]

for path in paths:
    ast.parse(path.read_text())

print("PASS: Python syntax")

assert (
    root / "shared/blockchain_install/runtime_binding.py"
).read_text() == (
    root / "seymour-blockchain-manager/data/shared/blockchain_install/runtime_binding.py"
).read_text()

assert (
    root / "shared/blockchain_install/runtime_binding_reconciler.py"
).read_text() == (
    root / "seymour-blockchain-manager/data/shared/blockchain_install/runtime_binding_reconciler.py"
).read_text()

print("PASS: root and Manager projections identical")

binding = (
    root / "shared/blockchain_install/runtime_binding.py"
).read_text()

assert "def parse_runtime_binding(" in binding
assert "def load_runtime_binding(" in binding

reconciler = (
    root / "shared/blockchain_install/runtime_binding_reconciler.py"
).read_text()

assert "def reconcile_installed_runtime_binding(" in reconciler
assert "materialize_runtime_binding(" in reconciler

print("PASS: canonical reconciliation contract")
PY

cmp -s \
  "$ROOT/shared/blockchain_install/runtime_binding.py" \
  "$PKG/payload/shared/blockchain_install/runtime_binding.py"

cmp -s \
  "$ROOT/shared/blockchain_install/runtime_binding_reconciler.py" \
  "$PKG/payload/shared/blockchain_install/runtime_binding_reconciler.py"

cmp -s \
  "$ROOT/seymour-blockchain-manager/data/shared/blockchain_install/runtime_binding.py" \
  "$PKG/payload/seymour-blockchain-manager/data/shared/blockchain_install/runtime_binding.py"

cmp -s \
  "$ROOT/seymour-blockchain-manager/data/shared/blockchain_install/runtime_binding_reconciler.py" \
  "$PKG/payload/seymour-blockchain-manager/data/shared/blockchain_install/runtime_binding_reconciler.py"

echo "PASS: package payload synchronized"

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

echo "SBP-075.4 DOCTOR PASS"
