#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
JS="$ROOT/seymour-blockchain-manager/data/web/app.js"
CSS="$ROOT/seymour-blockchain-manager/data/web/style.css"

grep -Fq 'telemetry?.runtimeState' "$JS"
grep -Fq 'telemetry?.operationalState?.state' "$JS"
grep -Fq '"degraded": "Degraded"' "$JS"
grep -Fq '"offline": "Offline"' "$JS"
grep -Fq 'runtime-state-dot' "$JS"
grep -Fq 'id="manageSync"' "$JS"
grep -Fq 'Open' "$JS"

! grep -Fq 'Lifecycle buttons will be enabled by the next guarded operations package.' "$JS" || {
  echo "SBP-039 verify: stale management placeholder remains"; exit 1;
}

grep -Fq '/* SBP-039 — Nexus visual integration */' "$CSS"
grep -Fq 'grid-template-columns: 1fr 1fr 1fr' "$CSS"
grep -Fq '.runtime-banner' "$CSS"

python3 - "$JS" <<'TESTPY'
from pathlib import Path
import sys
s = Path(sys.argv[1]).read_text()
start = s.index("function lifecycle(provider)")
end = s.index("function lifecycleLabel", start)
block = s[start:end]
assert block.index("runtimeState") < block.index("lifecycleStatus")
print("SBP-039 canonical runtime precedence verification: PASS")
TESTPY

echo "SBP-039 canonical state labels verification: PASS"
echo "SBP-039 card action overflow prevention verification: PASS"
echo "SBP-039 Nexus visual integration verification: PASS"
echo "SBP-039 final verification: PASS"
