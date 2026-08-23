#!/usr/bin/env bash
set -euo pipefail

PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT="$(cd "$PKG/../.." && pwd)"

ROOT_CONTROL="$ROOT/shared/umbrel_control"
MANAGER_CONTROL="$ROOT/seymour-blockchain-manager/data/shared/umbrel_control"

INSTALLED_CONTROL="/home/umbrel/umbrel/app-data/seymour-blockchain-manager/data/shared/umbrel_control"

echo "===== SBP-075.5 INSTALL ====="

"$PKG/scripts/doctor.sh"

install -D -m 0644 \
  "$PKG/payload/shared/umbrel_control/bridge.py" \
  "$ROOT_CONTROL/bridge.py"

install -D -m 0644 \
  "$PKG/payload/shared/umbrel_control/http_client.py" \
  "$ROOT_CONTROL/http_client.py"

echo "PASS: host control projection installed"

install -D -m 0644 \
  "$PKG/payload/seymour-blockchain-manager/data/shared/umbrel_control/bridge.py" \
  "$MANAGER_CONTROL/bridge.py"

install -D -m 0644 \
  "$PKG/payload/seymour-blockchain-manager/data/shared/umbrel_control/http_client.py" \
  "$MANAGER_CONTROL/http_client.py"

echo "PASS: Manager source projection installed"

test -d "$INSTALLED_CONTROL"

install -m 0644 \
  "$PKG/payload/seymour-blockchain-manager/data/shared/umbrel_control/bridge.py" \
  "$INSTALLED_CONTROL/bridge.py"

install -m 0644 \
  "$PKG/payload/seymour-blockchain-manager/data/shared/umbrel_control/http_client.py" \
  "$INSTALLED_CONTROL/http_client.py"

find "$INSTALLED_CONTROL" \
  -type d \
  -name '__pycache__' \
  -prune \
  -exec rm -rf {} + \
  2>/dev/null || true

echo "PASS: installed Manager projection installed"

echo "SBP-075.5 INSTALL PASS"
