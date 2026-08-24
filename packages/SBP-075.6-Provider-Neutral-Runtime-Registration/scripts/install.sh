#!/usr/bin/env bash
set -euo pipefail

PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT="$(cd "$PKG/../.." && pwd)"

SOURCE="$PKG/payload/seymour-blockchain-manager/data/web/nexus_integration.py"
REPO_TARGET="$ROOT/seymour-blockchain-manager/data/web/nexus_integration.py"
INSTALLED_TARGET="/home/umbrel/umbrel/app-data/seymour-blockchain-manager/data/web/nexus_integration.py"

echo "===== SBP-075.6 INSTALL ====="

"$PKG/scripts/doctor.sh"

test -f "$REPO_TARGET"
test -f "$INSTALLED_TARGET"

install -m 0644 "$SOURCE" "$REPO_TARGET"
echo "PASS: repository projection installed"

install -m 0644 "$SOURCE" "$INSTALLED_TARGET"
echo "PASS: installed Manager projection installed"

echo "SBP-075.6 INSTALL PASS"
