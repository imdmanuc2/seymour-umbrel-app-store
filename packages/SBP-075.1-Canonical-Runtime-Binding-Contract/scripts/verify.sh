#!/usr/bin/env bash
set -euo pipefail

PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT="$(cd "$PKG/../.." && pwd)"
TARGET="$ROOT/shared/blockchain_install/runtime_binding.py"

echo "===== SBP-075.1 VERIFY ====="

test -f "$TARGET"

python3 -m py_compile "$TARGET"

cmp -s \
  "$PKG/payload/shared/blockchain_install/runtime_binding.py" \
  "$TARGET"

echo "PASS: installed contract matches package payload"

grep -q \
  'SINGLE_PATH = "single-path"' \
  "$TARGET"

grep -q \
  'HYBRID_BLOCKS = "hybrid-blocks"' \
  "$TARGET"

echo "PASS: both canonical binding modes present"

echo
echo "===== LIVE RUNTIME NON-INTERFERENCE ====="

sudo docker inspect seymour-monero-node_node_1 \
  --format 'status={{.State.Status}} health={{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}} restarts={{.RestartCount}}'

echo
echo "SBP-075.1 VERIFY PASS"
