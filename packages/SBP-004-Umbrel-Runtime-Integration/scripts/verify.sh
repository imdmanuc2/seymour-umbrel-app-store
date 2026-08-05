#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 \
  "$ROOT/tests/verify.py" \
  "$REPO"

"$REPO/scripts/seymour-umbrel-runtime" \
  apps \
  >/tmp/sbp-004-runtime-apps.json

python3 - <<'PY'
import json
from pathlib import Path

payload = json.loads(
    Path(
        "/tmp/sbp-004-runtime-apps.json"
    ).read_text()
)

assert payload["sourceCount"] >= 2
assert "seymour-bch-node" in payload["sourceApps"]

print(
    "SBP-004 runtime CLI verification: PASS"
)
PY

echo "SBP-004 final verification: PASS"
