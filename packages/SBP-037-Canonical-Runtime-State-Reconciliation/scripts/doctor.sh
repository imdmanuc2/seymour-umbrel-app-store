#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"

for f in   "$ROOT/shared/app_lifecycle/engine.py"   "$ROOT/shared/app_lifecycle/model.py"   "$ROOT/shared/app_lifecycle/executor.py"   "$ROOT/shared/app_lifecycle/__init__.py"   "$ROOT/seymour-blockchain-manager/data/web/lifecycle_routes.py"   "$ROOT/seymour-blockchain-manager/docker-compose.yml"
do
  [[ -f "$f" ]] || { echo "SBP-037 doctor: missing required file: $f"; exit 1; }
done

grep -Fq 'BCH_STATUS_URL:' "$ROOT/seymour-blockchain-manager/docker-compose.yml" || {
  echo "SBP-037 doctor: BCH_STATUS_URL contract missing"; exit 1;
}
grep -Fq 'def read_state(self, app_id: str)' "$ROOT/shared/app_lifecycle/executor.py" || {
  echo "SBP-037 doctor: LifecycleExecutor read_state anchor missing"; exit 1;
}

python3 -m py_compile   "$ROOT/shared/app_lifecycle/engine.py"   "$ROOT/shared/app_lifecycle/model.py"   "$ROOT/shared/app_lifecycle/executor.py"   "$ROOT/seymour-blockchain-manager/data/web/lifecycle_routes.py"

echo "SBP-037 doctor: canonical runtime/lifecycle anchors PASS"
echo "SBP-037 doctor: PASS"
