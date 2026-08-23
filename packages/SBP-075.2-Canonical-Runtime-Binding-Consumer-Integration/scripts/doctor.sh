#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
PKG="$ROOT/packages/SBP-075.2-Canonical-Runtime-Binding-Consumer-Integration"
FILE="$PKG/payload/seymour-blockchain-manager/data/web/installer.py"

echo "===== SBP-075.2 DOCTOR ====="

test -f "$FILE"
echo "PASS: installer payload exists"

PYTHONDONTWRITEBYTECODE=1 \
python3 - "$FILE" <<'PY'
from pathlib import Path
import ast
import sys

path = Path(sys.argv[1])
text = path.read_text()

ast.parse(text)

required = [
    "RuntimeBinding",
    "RuntimeBindingMode",
    "serialize_runtime_binding",
    "runtime_binding.environment()",
    "_write_runtime_binding_config(",
]

for value in required:
    if value not in text:
        raise SystemExit(
            f"Missing canonical consumer contract: {value}"
        )

print("PASS: Python syntax")
print("PASS: canonical consumer references")
PY

if grep -q \
  '"SEYMOUR_BLOCKCHAIN_DATA_PATH": str(data_path)' \
  "$FILE"
then
  echo "ERROR: legacy manual DATA_PATH export remains"
  exit 1
fi

if grep -q \
  '"SEYMOUR_BLOCKCHAIN_LOCAL_DATA_PATH": str(runtime_data_path)' \
  "$FILE"
then
  echo "ERROR: legacy manual LOCAL_DATA_PATH export remains"
  exit 1
fi

echo "PASS: duplicate manual environment contract removed"

if grep -q \
  'if value.provider_id == "bitcoin-cash-mainnet":.*_write_runtime_binding_config' \
  "$FILE"
then
  echo "ERROR: BCH-only binding persistence remains"
  exit 1
fi

echo "PASS: canonical persistence is provider-neutral"

if find "$PKG" -type d -name __pycache__ -print -quit | grep -q .
then
  echo "ERROR: bytecode directory found"
  exit 1
fi

if find "$PKG" -type f \( -name '*.pyc' -o -name '*.pyo' \) -print -quit | grep -q .
then
  echo "ERROR: bytecode artifact found"
  exit 1
fi

echo "PASS: package bytecode-free"
echo "SBP-075.2 DOCTOR PASS"
