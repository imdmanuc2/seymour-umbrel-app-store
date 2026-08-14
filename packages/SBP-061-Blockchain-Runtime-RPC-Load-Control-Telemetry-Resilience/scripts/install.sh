#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
"$PKG/scripts/doctor.sh" "$ROOT"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$ROOT/backups/sbp-061-$STAMP"
mkdir -p "$BACKUP" "$ROOT/tests"
cp -a "$ROOT/seymour-blockchain-manager/data/web/bch_runtime_probe.py" "$BACKUP/bch_runtime_probe.py"
cp -a "$ROOT/seymour-blockchain-manager/data/web/telemetry.py" "$BACKUP/telemetry.py"
python3 "$PKG/scripts/patch.py"
cp "$PKG/payload/tests/test_bch_runtime_cache.py" "$ROOT/tests/test_bch_runtime_cache.py"

INSTALLED="/home/umbrel/umbrel/app-data/seymour-blockchain-manager/data/web"
if [ -d "$INSTALLED" ]; then
  mkdir -p "$BACKUP/installed"
  [ ! -f "$INSTALLED/bch_runtime_probe.py" ] || cp -a "$INSTALLED/bch_runtime_probe.py" "$BACKUP/installed/bch_runtime_probe.py"
  [ ! -f "$INSTALLED/telemetry.py" ] || cp -a "$INSTALLED/telemetry.py" "$BACKUP/installed/telemetry.py"
  cp "$ROOT/seymour-blockchain-manager/data/web/bch_runtime_probe.py" "$INSTALLED/bch_runtime_probe.py"
  cp "$ROOT/seymour-blockchain-manager/data/web/telemetry.py" "$INSTALLED/telemetry.py"
  echo "SBP-061 installed Blockchain Manager code synchronized: PASS"
fi

echo "Backup: $BACKUP"
echo "SBP-061 process-wide runtime snapshot cache installed: PASS"
echo "SBP-061 single-flight probe coalescing installed: PASS"
echo "SBP-061 last-known-good telemetry continuity installed: PASS"
echo "SBP-061 install: PASS"
echo "No BCH runtime was restarted and no blockchain data was modified."
