#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
ROOT="$(
  cd "$(dirname "${BASH_SOURCE[0]}")/.."
  pwd
)"

python3 \
  "$ROOT/tests/verify.py" \
  "$REPO"

"$REPO/scripts/seymour-install-bch" \
  --minimum-free-bytes 1 \
  >/tmp/sbp-006-plan.json

python3 - <<'PY'
import json
from pathlib import Path

payload = json.loads(
    Path(
        "/tmp/sbp-006-plan.json"
    ).read_text()
)

assert payload["mode"] == "plan"
assert (
    payload["requiredConfirmation"]
    == "INSTALL-seymour-bch-node"
)
assert (
    payload["automaticUninstallOnFailure"]
    is False
)

print(
    "SBP-006 guarded install plan "
    "verification: PASS"
)
PY

echo "SBP-006 final verification: PASS"
