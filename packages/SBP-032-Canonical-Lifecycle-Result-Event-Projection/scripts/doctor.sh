#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

[[ -d "$ROOT/.git" ]] || { echo "SBP-032 doctor: FAIL — repository not found: $ROOT"; exit 1; }
[[ -f "$ROOT/shared/app_lifecycle/executor.py" ]] || { echo "SBP-032 doctor: FAIL — SBP-031 lifecycle executor not installed"; exit 1; }
[[ -f "$ROOT/shared/contracts/app-lifecycle-execution-v1.json" ]] || { echo "SBP-032 doctor: FAIL — SBP-031 execution contract not installed"; exit 1; }
[[ -f "$ROOT/shared/app_lifecycle/engine.py" ]] || { echo "SBP-032 doctor: FAIL — SBP-030 lifecycle engine not installed"; exit 1; }

if grep -R --line-number -E 'docker[[:space:]]+(start|stop|restart|rm|compose[[:space:]]+(up|down|restart))' \
    "$PKG/payload/shared/app_lifecycle" >/tmp/sbp032-direct-docker.txt 2>/dev/null; then
  cat /tmp/sbp032-direct-docker.txt
  echo "SBP-032 doctor: FAIL — direct Docker lifecycle command detected in payload"
  exit 1
fi

python3 -m py_compile \
  "$PKG/payload/shared/app_lifecycle/projection.py" \
  "$PKG/payload/shared/app_lifecycle/__init__.py" \
  "$PKG/payload/tests/test_sbp032_projection.py" \
  "$PKG/payload/tests/test_sbp032_contract.py"

echo "SBP-032 doctor: canonical projection payload compile PASS"
echo "SBP-032 doctor: PASS"
