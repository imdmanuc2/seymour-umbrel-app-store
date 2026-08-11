#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
JS="$ROOT/seymour-blockchain-manager/data/web/app.js"
CSS="$ROOT/seymour-blockchain-manager/data/web/style.css"

grep -Fq 'async function fetchJsonWithTimeout(' "$JS"
grep -Fq 'controller.abort()' "$JS"
grep -Fq 'error: "request-timeout"' "$JS"
grep -Fq 'async function loadLifecycleHistory()' "$JS"
grep -Fq 'function renderLifecycleTimeline(target, payload)' "$JS"
grep -Fq 'function renderDiagnostics(target, payload)' "$JS"
grep -Fq 'function renderLogs(target, payload)' "$JS"
grep -Fq 'id="opsHistoryView"' "$JS"
grep -Fq 'id="opsDiagnosticsView"' "$JS"
grep -Fq 'id="opsLogsView"' "$JS"

# Lifecycle must still use the one canonical endpoint.
grep -Fq '"/api/lifecycle/operation"' "$JS"
if grep -Eq 'fetch\(`/api/lifecycle/\$\{action\}`' "$JS"; then
  echo "SBP-044 verify: legacy lifecycle route found"
  exit 1
fi

# Planning/execution must preserve guarded semantics.
python3 - "$JS" <<'TESTPY'
from pathlib import Path
import sys

s = Path(sys.argv[1]).read_text()

assert "return lifecycleRequest(provider, action, false, null)" in s
assert "true,\n    confirmation" in s
assert "fetchJsonWithTimeout(" in s
assert "Request exceeded" in s

# Preserve SBP-041 runtime presentation stabilization.
assert 'current.state === "syncing"' in s
assert '["degraded", "unknown"].includes(rawState)' in s

# History is refreshed after a successful lifecycle plan.
plan_start = s.index("async function planLifecycle(action)")
plan_end = s.index('document.getElementById("opsStart")', plan_start)
plan_block = s[plan_start:plan_end]
assert "await loadLifecycleHistory();" in plan_block

print("SBP-044 guarded lifecycle preservation: PASS")
print("SBP-044 timeout handling verification: PASS")
print("SBP-044 post-plan evidence refresh verification: PASS")
print("SBP-044 runtime stabilization preservation: PASS")
TESTPY

grep -Fq '/* SBP-044 — operations evidence timeline */' "$CSS"
grep -Fq '.ops-timeline' "$CSS"
grep -Fq '.ops-diagnostic-grid' "$CSS"
grep -Fq '.ops-log-view' "$CSS"

echo "SBP-044 Operations evidence styling verification: PASS"
echo "SBP-044 final verification: PASS"
echo "No live Umbrel lifecycle write action was executed by verify.sh."
