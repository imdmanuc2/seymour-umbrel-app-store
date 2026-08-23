#!/usr/bin/env bash
set -euo pipefail

PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT="$(cd "$PKG/../.." && pwd)"

CANONICAL="$ROOT/shared/blockchain_install/runtime_binding.py"
PAYLOAD_CANONICAL="$PKG/payload/shared/blockchain_install/runtime_binding.py"
PAYLOAD_MANAGER="$PKG/payload/seymour-blockchain-manager/data/shared/blockchain_install/runtime_binding.py"

echo "===== SBP-075.1.1 DOCTOR ====="

test -f "$CANONICAL"
echo "PASS: canonical contract exists"

python3 - \
  "$CANONICAL" \
  "$PAYLOAD_CANONICAL" \
  "$PAYLOAD_MANAGER" <<'PYTHON'
from pathlib import Path
import sys

for filename in sys.argv[1:]:
    source = Path(filename).read_text()
    compile(source, filename, "exec")

print("PASS: Python syntax")
PYTHON

cmp "$CANONICAL" "$PAYLOAD_CANONICAL"
cmp "$PAYLOAD_CANONICAL" "$PAYLOAD_MANAGER"

echo "PASS: package projections identical"

grep -q \
  'SINGLE_PATH = "single-path"' \
  "$PAYLOAD_MANAGER"

grep -q \
  'HYBRID_BLOCKS = "hybrid-blocks"' \
  "$PAYLOAD_MANAGER"

echo "PASS: canonical binding modes present"

echo "SBP-075.1.1 DOCTOR PASS"
