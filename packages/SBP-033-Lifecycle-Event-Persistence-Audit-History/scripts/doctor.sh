#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

[[ -d "$ROOT/.git" ]] || { echo "SBP-033 doctor: FAIL — repository not found: $ROOT"; exit 1; }
[[ -f "$ROOT/shared/app_lifecycle/projection.py" ]] || { echo "SBP-033 doctor: FAIL — SBP-032 projection not installed"; exit 1; }
[[ -f "$ROOT/shared/contracts/app-lifecycle-event-v1.json" ]] || { echo "SBP-033 doctor: FAIL — SBP-032 event contract not installed"; exit 1; }
[[ -f "$ROOT/shared/app_lifecycle/executor.py" ]] || { echo "SBP-033 doctor: FAIL — SBP-031 lifecycle executor not installed"; exit 1; }

if grep -R --line-number -E 'docker[[:space:]]+(start|stop|restart|rm|compose[[:space:]]+(up|down|restart))' \
    "$PKG/payload/shared/app_lifecycle" >/tmp/sbp033-direct-docker.txt 2>/dev/null; then
  cat /tmp/sbp033-direct-docker.txt
  echo "SBP-033 doctor: FAIL — direct Docker lifecycle command detected in payload"
  exit 1
fi

python3 -m py_compile \
  "$PKG/payload/shared/app_lifecycle/audit.py" \
  "$PKG/payload/shared/app_lifecycle/__init__.py" \
  "$PKG/payload/tests/test_sbp033_audit.py" \
  "$PKG/payload/tests/test_sbp033_contract.py"

echo "SBP-033 doctor: audit payload compile PASS"
echo "SBP-033 doctor: PASS"
