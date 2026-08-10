#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
WEB="$ROOT/seymour-blockchain-manager/data/web"
JS="$WEB/app.js"
HTML="$WEB/index.html"

grep -Fq 'function setText(id, value)' "$JS"
grep -Fq 'setText(' "$JS"
grep -Fq 'renderOperationalSummary();' "$JS"
grep -Fq 'renderRuntimeFocus();' "$JS"
grep -Fq 'renderProviders();' "$JS"

# Old summary IDs must not be written by JS after SBP-042 removed them from HTML.
for id in providerCount liveCount plannedCount; do
  if grep -Fq "getElementById(\"$id\")" "$JS"; then
    echo "SBP-042.1 verify: stale DOM write remains for $id"
    exit 1
  fi
done
echo "SBP-042.1 removed-summary DOM contract verification: PASS"

# Every critical operational summary target referenced by the new UI must exist.
python3 - "$JS" "$HTML" <<'TESTPY'
from pathlib import Path
import re
import sys

js = Path(sys.argv[1]).read_text()
html = Path(sys.argv[2]).read_text()

required = [
    "installedCount",
    "syncingCount",
    "runningCount",
    "rpcReachableCount",
    "peerCount",
    "runtimeDiskUsed",
    "runtimeFocus",
    "providerGrid",
    "filters",
    "search",
    "catalogStatus",
]

missing = [item for item in required if f'id="{item}"' not in html]
assert not missing, f"Missing HTML ids: {missing}"

# Preserve runtime stabilization.
assert 'current.state === "syncing"' in js
assert '["degraded", "unknown"].includes(rawState)' in js

# Legacy summary IDs should be absent from new HTML.
for obsolete in ("providerCount", "liveCount", "plannedCount"):
    assert f'id="{obsolete}"' not in html

print("SBP-042.1 critical DOM id audit: PASS")
print("SBP-042.1 SBP-041 stabilization preservation: PASS")
TESTPY

echo "SBP-042.1 frontend boot contract verification: PASS"
echo "SBP-042.1 final verification: PASS"
echo "No live Umbrel lifecycle write action was executed by verify.sh."
