#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

[[ -d "$ROOT/.git" ]] || { echo "SBP-031 doctor: FAIL — repository not found: $ROOT"; exit 1; }
[[ -f "$ROOT/shared/app_lifecycle/engine.py" ]] || { echo "SBP-031 doctor: FAIL — SBP-030 lifecycle engine not installed"; exit 1; }
[[ -f "$ROOT/shared/app_lifecycle/model.py" ]] || { echo "SBP-031 doctor: FAIL — SBP-030 lifecycle model not installed"; exit 1; }
[[ -f "$ROOT/shared/umbrel_control/bridge.py" ]] || { echo "SBP-031 doctor: FAIL — native Umbrel control bridge not found"; exit 1; }
[[ -f "$ROOT/shared/umbrel_control/native-client.ts" ]] || { echo "SBP-031 doctor: FAIL — native Umbrel helper not found"; exit 1; }

if grep -R --line-number -E 'docker[[:space:]]+(start|stop|restart|rm|compose[[:space:]]+(up|down|restart))' \
    "$PKG/payload/shared/app_lifecycle" "$PKG/payload/scripts" >/tmp/sbp031-direct-docker.txt 2>/dev/null; then
  cat /tmp/sbp031-direct-docker.txt
  echo "SBP-031 doctor: FAIL — direct Docker lifecycle command detected in payload"
  exit 1
fi

python3 -m py_compile \
  "$PKG/payload/shared/app_lifecycle/executor.py" \
  "$PKG/payload/shared/app_lifecycle/__init__.py" \
  "$PKG/payload/scripts/seymour-app-lifecycle"

python3 - <<PY
import sys
from pathlib import Path
sys.path.insert(0, "$ROOT")
from shared.umbrel_control import UmbrelAppControlBridge
assert UmbrelAppControlBridge is not None
print("SBP-031 doctor: existing native Umbrel bridge import PASS")
PY

echo "SBP-031 doctor: PASS"
