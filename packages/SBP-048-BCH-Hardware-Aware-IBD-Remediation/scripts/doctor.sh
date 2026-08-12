#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"

for f in \
  "$ROOT/seymour-bch-node/data/status/provisioning.py" \
  "$ROOT/seymour-bch-node/data/node/entrypoint.sh" \
  "$ROOT/seymour-bch-node/data/status/templates/provision.html"
do
  [[ -f "$f" ]] || { echo "SBP-048 doctor: missing $f"; exit 1; }
done

grep -Fq 'txindex' "$ROOT/seymour-bch-node/data/status/provisioning.py"
grep -Fq 'BCH_TXINDEX' "$ROOT/seymour-bch-node/data/node/entrypoint.sh"

echo "SBP-048 doctor: BCH txindex policy anchors PASS"
echo "SBP-048 doctor: PASS"
