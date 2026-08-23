#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
PKG="$ROOT/packages/SBP-075.2-Canonical-Runtime-Binding-Consumer-Integration"

SOURCE="$PKG/payload/seymour-blockchain-manager/data/web/installer.py"
TARGET="$ROOT/seymour-blockchain-manager/data/web/installer.py"

echo "===== SBP-075.2 INSTALL ====="

"$PKG/scripts/doctor.sh"

mkdir -p "$(dirname "$TARGET")"

if [[ -f "$TARGET" ]]; then
  cp \
    "$TARGET" \
    "${TARGET}.before-sbp-075.2"
fi

cp "$SOURCE" "$TARGET"

echo "PASS: canonical runtime binding consumer installed"
echo "SBP-075.2 INSTALL PASS"
