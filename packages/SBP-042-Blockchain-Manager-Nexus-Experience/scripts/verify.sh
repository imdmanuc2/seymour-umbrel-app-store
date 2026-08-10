#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
WEB="$ROOT/seymour-blockchain-manager/data/web"
JS="$WEB/app.js"
HTML="$WEB/index.html"
CSS="$WEB/style.css"

grep -Fq 'function renderOperationalSummary()' "$JS"
grep -Fq 'function renderRuntimeFocus()' "$JS"
grep -Fq 'renderOperationalSummary();' "$JS"
grep -Fq 'renderRuntimeFocus();' "$JS"
grep -Fq 'provider.availability !== "live"' "$JS"
grep -Fq 'id="runtimeFocus"' "$HTML"
grep -Fq 'id="installedCount"' "$HTML"
grep -Fq 'id="syncingCount"' "$HTML"
grep -Fq 'id="rpcReachableCount"' "$HTML"
grep -Fq 'Provider catalog' "$HTML"
grep -Fq '/* SBP-042 — Nexus experience */' "$CSS"
grep -Fq '.runtime-focus-card' "$CSS"
grep -Fq '.operational-summary' "$CSS"
grep -Fq '.catalog-card' "$CSS"

python3 - "$JS" <<'TESTPY'
from pathlib import Path
import sys

s = Path(sys.argv[1]).read_text()

assert "presentedRuntime(provider)" in s
assert "RUNTIME_PRESENTATION_GRACE_MS" in s
assert "renderRuntimeFocus()" in s
assert "renderOperationalSummary()" in s

# SBP-042 must preserve the presentation stabilization from SBP-041.
assert 'current.state === "syncing"' in s
assert '["degraded", "unknown"].includes(rawState)' in s

print("SBP-042 SBP-041 stabilization preservation: PASS")
print("SBP-042 operational-first rendering verification: PASS")
TESTPY

echo "SBP-042 Nexus experience CSS verification: PASS"
echo "SBP-042 final verification: PASS"
echo "No live Umbrel lifecycle write action was executed by verify.sh."
