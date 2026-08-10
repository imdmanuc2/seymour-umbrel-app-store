#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
APP="$ROOT/seymour-blockchain-manager/data/web/app.py"
COMPOSE="$ROOT/seymour-blockchain-manager/docker-compose.yml"
for p in \
  "$ROOT/shared/app_lifecycle/api.py" \
  "$ROOT/shared/app_lifecycle/operations.py" \
  "$ROOT/shared/app_lifecycle/audit.py" \
  "$ROOT/shared/app_lifecycle/executor.py" \
  "$ROOT/shared/umbrel_control/bridge.py" \
  "$APP" \
  "$COMPOSE"; do
  [[ -f "$p" ]] || { echo "SBP-036 doctor: missing dependency: $p" >&2; exit 1; }
done
python3 -m py_compile "$APP"
grep -q 'from lifecycle import GuardedLifecycleService, LifecycleAction' "$APP" || {
  grep -q 'from lifecycle_routes import LIFECYCLE_HTTP' "$APP" || {
    echo "SBP-036 doctor: lifecycle route anchor not found" >&2; exit 1;
  }
}
echo "SBP-036 doctor: Blockchain Manager HTTP anchors PASS"
echo "SBP-036 doctor: PASS"
