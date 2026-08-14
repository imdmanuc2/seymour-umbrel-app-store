#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
BACKUP="$(find "$ROOT/backups" -maxdepth 1 -type d -name 'sbp-060.7-*' | sort | tail -1)"
test -n "$BACKUP"
cp -a "$BACKUP/bridge.py" "$ROOT/shared/umbrel_control/bridge.py"
rm -f "$ROOT/shared/blockchain_install/start_guard.py" "$ROOT/tests/test_start_guard.py"
echo "SBP-060.7 rollback: PASS"
echo "No blockchain runtime or data was modified."
