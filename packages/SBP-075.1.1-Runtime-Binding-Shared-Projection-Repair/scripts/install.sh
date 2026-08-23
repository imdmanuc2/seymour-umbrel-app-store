#!/usr/bin/env bash
set -euo pipefail

PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT="$(cd "$PKG/../.." && pwd)"

SOURCE="$PKG/payload/shared/blockchain_install/runtime_binding.py"

CANONICAL="$ROOT/shared/blockchain_install/runtime_binding.py"
MANAGER="$ROOT/seymour-blockchain-manager/data/shared/blockchain_install/runtime_binding.py"

echo "===== SBP-075.1.1 INSTALL ====="

"$PKG/scripts/doctor.sh"

mkdir -p "$(dirname "$MANAGER")"

if [[ -f "$MANAGER" ]]; then
    cp -a \
      "$MANAGER" \
      "$MANAGER.before-sbp-075.1.1-$(date -u +%Y%m%dT%H%M%SZ)"
fi

install -m 0644 "$SOURCE" "$CANONICAL"
install -m 0644 "$SOURCE" "$MANAGER"

echo "PASS: runtime binding shared projection installed"
echo "SBP-075.1.1 INSTALL PASS"
