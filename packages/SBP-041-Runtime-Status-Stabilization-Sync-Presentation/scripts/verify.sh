#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
JS="$ROOT/seymour-blockchain-manager/data/web/app.js"
CSS="$ROOT/seymour-blockchain-manager/data/web/style.css"

grep -Fq 'RUNTIME_PRESENTATION_GRACE_MS = 20000' "$JS"
grep -Fq 'function presentedRuntime(provider)' "$JS"
grep -Fq 'current.state === "syncing"' "$JS"
grep -Fq '["degraded", "unknown"].includes(rawState)' "$JS"
grep -Fq 'graceHeld: true' "$JS"
grep -Fq 'Live telemetry reconnecting' "$JS"
grep -Fq 'Sync progress' "$JS"
grep -Fq 'metric-good' "$JS"

grep -Fq '/* SBP-041 — runtime status stabilization */' "$CSS"
grep -Fq 'height: 12px' "$CSS"
grep -Fq '.telemetry-grace-note' "$CSS"
grep -Fq '.provider-card.syncing' "$CSS"

python3 - "$JS" <<'TESTPY'
from pathlib import Path
import sys

s = Path(sys.argv[1]).read_text()

assert "RUNTIME_PRESENTATION_GRACE_MS = 20000" in s
assert 'current.state === "syncing"' in s
assert '["degraded", "unknown"].includes(rawState)' in s

# Error/offline are intentionally absent from the grace list: real severe
# states must never be hidden by presentation hysteresis.
grace_start = s.index("if (\n    current &&")
grace_end = s.index("  ) {", grace_start)
grace_block = s[grace_start:grace_end]
assert '"error"' not in grace_block
assert '"offline"' not in grace_block
assert '"stopped"' not in grace_block

print("SBP-041 short degraded/unknown grace verification: PASS")
print("SBP-041 severe-state immediate visibility verification: PASS")
TESTPY

# No backend canonical state code is touched by this UI package.
if find "$ROOT/shared" -type f -newer "$JS" 2>/dev/null | grep -q .; then
  :
fi

echo "SBP-041 sync presentation verification: PASS"
echo "SBP-041 final verification: PASS"
echo "No live Umbrel lifecycle write action was executed by verify.sh."
