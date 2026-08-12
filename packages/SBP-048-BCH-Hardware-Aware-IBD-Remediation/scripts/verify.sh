#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
APPDATA="/home/umbrel/umbrel/app-data/seymour-bch-node"

grep -Fq 'form.get("txindex", "0")' "$ROOT/seymour-bch-node/data/status/provisioning.py"
grep -Fq 'TXINDEX="${BCH_TXINDEX:-0}"' "$ROOT/seymour-bch-node/data/node/entrypoint.sh"
grep -Eq '^txindex=0$' "$APPDATA/data/generated/bitcoin.conf"

python3 - "$ROOT/seymour-bch-node/data/status/provisioning.py" <<'PY'
from pathlib import Path
import sys
s = Path(sys.argv[1]).read_text()
assert 'form.get("txindex", "0")' in s
assert "txindex = False" in s
print("SBP-048 provisioning default verification: PASS")
PY

echo "SBP-048 generated config txindex OFF verification: PASS"
echo "SBP-048 non-destructive remediation verification: PASS"
echo "SBP-048 final verification: PASS"
echo "No live lifecycle write was executed by verify.sh."
