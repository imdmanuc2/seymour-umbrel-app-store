#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
MARKER="$ROOT/backups/sbp-040-latest"
WEB="$ROOT/seymour-blockchain-manager/data/web"
COMPOSE="$ROOT/seymour-blockchain-manager/docker-compose.yml"
INSTALLED="/home/umbrel/umbrel/app-data/seymour-blockchain-manager"
[[ -f "$MARKER" ]] || { echo "SBP-040 rollback: backup marker missing"; exit 1; }
BACKUP="$(cat "$MARKER")"
cp -a "$BACKUP/data/web/telemetry.py" "$WEB/telemetry.py"
cp -a "$BACKUP/data/web/bch_runtime_probe.py" "$WEB/bch_runtime_probe.py"
cp -a "$BACKUP/docker-compose.yml" "$COMPOSE"
if [[ -d "$INSTALLED/data/web" ]]; then
  cp -a "$WEB/telemetry.py" "$INSTALLED/data/web/telemetry.py"
  cp -a "$WEB/bch_runtime_probe.py" "$INSTALLED/data/web/bch_runtime_probe.py"
fi
if [[ -f "$INSTALLED/docker-compose.yml" ]]; then cp -a "$COMPOSE" "$INSTALLED/docker-compose.yml"; fi
echo "SBP-040 rollback: dashboard/runtime files restored"
echo "Blockchain Manager restart was NOT performed by rollback.sh."
echo "SBP-040 rollback: PASS"
