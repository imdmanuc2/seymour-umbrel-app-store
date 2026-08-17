#!/usr/bin/env bash
set -euo pipefail
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO="$(cd "$PKG/../.." && pwd)"
MGR_LIVE="/home/umbrel/umbrel/app-data/seymour-blockchain-manager/data/web"
BCH_LIVE="/home/umbrel/umbrel/app-data/seymour-bch-node/data/status"

echo "SBP-063.3.8 verify: runtime state and storage telemetry accuracy"
python3 -m py_compile \
  "$REPO/seymour-blockchain-manager/data/web/telemetry.py" \
  "$REPO/seymour-bch-node/data/status/app.py" \
  "$MGR_LIVE/telemetry.py" \
  "$BCH_LIVE/app.py"
echo "SBP-063.3.8 Python compile contract: PASS"

grep -q 'authoritativeLifecycle: true' "$REPO/seymour-blockchain-manager/data/web/app.js"
grep -q 'elif not running:' "$REPO/seymour-blockchain-manager/data/web/telemetry.py"
grep -q 'runtime_state = "stopped"' "$REPO/seymour-blockchain-manager/data/web/telemetry.py"
echo "SBP-063.3.8 lifecycle precedence contract: PASS"

grep -q 'def runtime_storage_footprint' "$REPO/seymour-bch-node/data/status/app.py"
grep -q 'one_filesystem=True' "$REPO/seymour-bch-node/data/status/app.py"
grep -q '"usageSemantics"' "$REPO/seymour-bch-node/data/status/app.py"
grep -q 'filesystemUsedBytes' "$REPO/seymour-bch-node/data/status/app.py"
echo "SBP-063.3.8 hybrid footprint contract: PASS"

cmp "$REPO/seymour-blockchain-manager/data/web/app.js" "$MGR_LIVE/app.js"
cmp "$REPO/seymour-blockchain-manager/data/web/telemetry.py" "$MGR_LIVE/telemetry.py"
cmp "$REPO/seymour-bch-node/data/status/app.py" "$BCH_LIVE/app.py"
echo "SBP-063.3.8 deployed checksum contract: PASS"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/node/blocks"
dd if=/dev/zero of="$TMP/node/local.bin" bs=1024 count=8 status=none
dd if=/dev/zero of="$TMP/node/blocks/block.bin" bs=1024 count=12 status=none
PYTHONPATH="$REPO/seymour-bch-node/data/status" \
BCH_DATA_PATH="$TMP/node" \
BCH_STORAGE_FOOTPRINT_TTL_SECONDS=900 \
python3 - <<'PY'
import app
p = app.runtime_storage_footprint()
assert p["usedBytes"] is not None and p["usedBytes"] > 0, p
assert p["localBytes"] is not None, p
assert p["blocksBytes"] is not None, p
assert p["usedBytes"] == p["localBytes"] + p["blocksBytes"], p
q = app.storage_payload()
assert q["usageSemantics"] == "runtime-footprint", q
assert q["usedBytes"] == p["usedBytes"], (q, p)
print("SBP-063.3.8 isolated footprint regression: PASS")
PY

echo "SBP-063.3.8 final verification: PASS"
echo "No live blockchain node runtime was modified."
