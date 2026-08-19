#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "SBP-074 doctor: checking Monero first-install storage prerequisites"

for f in   "$ROOT/shared/provider_catalog/providers.v1.json"   "$ROOT/seymour-monero-node/hooks/pre-install"   "$ROOT/seymour-monero-node/docker-compose.yml"   "$PKG/scripts/seymour-runtime-storage-provision"
do
  test -f "$f" || { echo "ERROR: missing $f"; exit 1; }
done

python3 -m py_compile "$PKG/scripts/patch.py"
bash -n "$ROOT/seymour-monero-node/hooks/pre-install"
bash -n "$PKG/scripts/seymour-runtime-storage-provision"

python3 - "$ROOT/shared/provider_catalog/providers.v1.json" <<'PY'
import json,sys
from pathlib import Path
data=json.loads(Path(sys.argv[1]).read_text())
xmr=next(p for p in data["providers"] if p["providerId"]=="monero-mainnet")
assert xmr["selectable"] is True
assert xmr["productionImage"]
assert xmr["runtime"]["appId"]=="seymour-monero-node"
PY

echo "SBP-074 Monero provider prerequisite: PASS"
echo "SBP-074 doctor: PASS"
