#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
BACKUP="$(find "$ROOT/backups" -maxdepth 1 -type d -name 'sbp-061-*' | sort | tail -1)"
test -n "$BACKUP"
cp -a "$BACKUP/bch_runtime_probe.py" "$ROOT/seymour-blockchain-manager/data/web/bch_runtime_probe.py"
cp -a "$BACKUP/telemetry.py" "$ROOT/seymour-blockchain-manager/data/web/telemetry.py"
INSTALLED="/home/umbrel/umbrel/app-data/seymour-blockchain-manager/data/web"
[ ! -f "$BACKUP/installed/bch_runtime_probe.py" ] || cp -a "$BACKUP/installed/bch_runtime_probe.py" "$INSTALLED/bch_runtime_probe.py"
[ ! -f "$BACKUP/installed/telemetry.py" ] || cp -a "$BACKUP/installed/telemetry.py" "$INSTALLED/telemetry.py"
rm -f "$ROOT/tests/test_bch_runtime_cache.py"
echo "SBP-061 rollback: PASS"
echo "No blockchain runtime or blockchain data was modified."
