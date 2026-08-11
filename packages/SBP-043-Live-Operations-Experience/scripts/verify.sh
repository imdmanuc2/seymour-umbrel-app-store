#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
JS="$ROOT/seymour-blockchain-manager/data/web/app.js"
CSS="$ROOT/seymour-blockchain-manager/data/web/style.css"

grep -Fq 'async function lifecycleRequest(provider, action, execute = false' "$JS"
grep -Fq 'fetch("/api/lifecycle/operation"' "$JS"
grep -Fq 'async function lifecyclePlan(provider, action)' "$JS"
grep -Fq 'async function lifecycleExecute(provider, action, confirmation)' "$JS"
grep -Fq 'function allowedLifecycleActions(runtimeState)' "$JS"
grep -Fq '/api/lifecycle/history?appId=' "$JS"
grep -Fq '/api/operations/diagnostics' "$JS"
grep -Fq '/api/operations/logs' "$JS"
grep -Fq '/api/operations/plan' "$JS"
grep -Fq '/api/operations/backup' "$JS"

# Frontend must not use the legacy lifecycle execution route.
if grep -Eq 'fetch\(`/api/lifecycle/\$\{action\}`' "$JS"; then
  echo "SBP-043 verify: legacy lifecycle execution route still present"
  exit 1
fi
echo "SBP-043 single canonical lifecycle HTTP route verification: PASS"

# No Docker lifecycle belongs in browser code.
if grep -Eqi 'docker[[:space:]].*(start|stop|restart|rm)|docker compose' "$JS"; then
  echo "SBP-043 verify: direct Docker lifecycle reference found"
  exit 1
fi
echo "SBP-043 direct Docker lifecycle prohibition: PASS"

python3 - "$JS" <<'TESTPY'
from pathlib import Path
import sys

s = Path(sys.argv[1]).read_text()

required = {
    "syncing": 'syncing: ["restart", "stop"]',
    "running": 'running: ["restart", "stop"]',
    "degraded": 'degraded: ["restart", "stop"]',
    "starting": 'starting: ["stop"]',
    "stopped": 'stopped: ["start"]',
    "offline": 'offline: ["start"]',
}

missing = [state for state, token in required.items() if token not in s]
assert not missing, f"Missing lifecycle UI policies: {missing}"

# Canonical plan must be execute=false and execution must carry confirmation.
assert "return lifecycleRequest(provider, action, false, null)" in s
assert "true,\n    confirmation" in s

# Preserve presentation stabilization.
assert 'current.state === "syncing"' in s
assert '["degraded", "unknown"].includes(rawState)' in s

print("SBP-043 lifecycle UI policy verification: PASS")
print("SBP-043 guarded plan-confirm-execute verification: PASS")
print("SBP-043 runtime stabilization preservation: PASS")
TESTPY

grep -Fq '/* SBP-043 — live operations experience */' "$CSS"
grep -Fq '.ops-runtime-strip' "$CSS"
grep -Fq '.ops-action-grid' "$CSS"
grep -Fq '.ops-result-card' "$CSS"

echo "SBP-043 Nexus Operations styling verification: PASS"
echo "SBP-043 final verification: PASS"
echo "No live Umbrel lifecycle write action was executed by verify.sh."
