#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 \
  "$ROOT/tests/verify.py" \
  "$REPO"

"$REPO/scripts/seymour-umbrel-app" \
  install \
  seymour-bch-node \
  >/tmp/sbp-005-plan.json

python3 - <<'PY'
import json
from pathlib import Path

payload = json.loads(
    Path(
        "/tmp/sbp-005-plan.json"
    ).read_text()
)

assert payload["mode"] == "plan"
assert payload["executed"] is False
assert (
    payload["result"]["requiredConfirmation"]
    == "INSTALL-seymour-bch-node"
)

print(
    "SBP-005 guarded plan verification: PASS"
)
PY

echo "SBP-005 final verification: PASS"
