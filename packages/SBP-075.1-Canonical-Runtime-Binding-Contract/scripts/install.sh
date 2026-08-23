#!/usr/bin/env bash
set -euo pipefail

PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT="$(cd "$PKG/../.." && pwd)"

SOURCE="$PKG/payload/shared/blockchain_install/runtime_binding.py"
TARGET="$ROOT/shared/blockchain_install/runtime_binding.py"

echo "===== SBP-075.1 INSTALL ====="

"$PKG/scripts/doctor.sh"

mkdir -p "$(dirname "$TARGET")"

if [[ -f "$TARGET" ]]; then
  cp -a \
    "$TARGET" \
    "$TARGET.before-sbp-075.1-$(date -u +%Y%m%dT%H%M%SZ)"
fi

install -m 0644 "$SOURCE" "$TARGET"

echo "PASS: canonical runtime binding contract installed"
echo "SBP-075.1 INSTALL PASS"
