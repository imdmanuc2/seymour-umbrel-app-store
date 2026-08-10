#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
APP_ID="seymour-blockchain-manager"
SRC="$ROOT/$APP_ID/docker-compose.yml"
INSTALLED="/home/umbrel/umbrel/app-data/$APP_ID/docker-compose.yml"

[[ -f "$SRC" ]] || { echo "SBP-036.3 doctor: missing repository compose"; exit 1; }
[[ -f "$INSTALLED" ]] || { echo "SBP-036.3 doctor: missing installed app-data compose"; exit 1; }

grep -Fq 'APP_PORT: 8080' "$SRC" || {
  echo "SBP-036.3 doctor: repository APP_PORT anchor missing"
  exit 1
}
grep -Fq 'APP_HOST:' "$SRC" || {
  echo "SBP-036.3 doctor: repository APP_HOST anchor missing"
  exit 1
}

grep -Fq 'SEYMOUR_PLATFORM_ROOT: /seymour-platform' "$SRC" || {
  echo "SBP-036.3 doctor: SBP-036 lifecycle runtime wiring missing from repository"
  exit 1
}
grep -Fq '/seymour-platform/shared:ro' "$SRC" || {
  echo "SBP-036.3 doctor: lifecycle shared mount missing from repository"
  exit 1
}

echo "SBP-036.3 doctor: repository/app-data compose targets detected PASS"
echo "SBP-036.3 doctor: PASS"
