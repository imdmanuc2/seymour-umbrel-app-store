#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
APP="$ROOT/seymour-blockchain-manager/data/web/app.js"
INSTALLED="/home/umbrel/umbrel/app-data/seymour-blockchain-manager/data/web/app.js"

echo "SBP-064.1 verify: blockchain live sync progress UI"

grep -q 'function formatSyncProgress(value)' "$APP"
grep -q 'normalized.toFixed(4)' "$APP"
grep -q 'normalized.toFixed(3)' "$APP"

echo "SBP-064.1 adaptive sync precision contract: PASS"

grep -q 'Live block progress' "$APP"
grep -q 'health.summary' "$APP"
grep -q 'health.detail' "$APP"

echo "SBP-064.1 live runtime card contract: PASS"

grep -q 'setInterval(refreshTelemetry, 5000)' "$APP"

COUNT="$(grep -c 'setInterval(refreshTelemetry, 5000)' "$APP")"
test "$COUNT" = "1"

echo "SBP-064.1 single telemetry polling contract: PASS"

cmp -s "$APP" "$INSTALLED"

echo "SBP-064.1 deployed checksum contract: PASS"

sudo docker inspect seymour-bch-node_node_1 \
  --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' \
  | grep -q '^running healthy$'

echo "SBP-064.1 BCH runtime safety contract: PASS"

sudo docker inspect seymour-bitcoin-node_node_1 \
  --format '{{.State.Status}}' \
  | grep -q '^running$'

echo "SBP-064.1 Bitcoin runtime safety contract: PASS"

echo "SBP-064.1 final verification: PASS"
echo "No live blockchain runtime was modified."
