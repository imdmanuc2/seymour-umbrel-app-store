#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PAYLOAD="$PKG/payload/seymour-monero-node"
TARGET="$REPO/seymour-monero-node"

"$PKG/scripts/doctor.sh"

if [[ -e "$TARGET" ]]; then
  echo "ERROR: canonical Monero app directory already exists: $TARGET"
  exit 1
fi

cp -a "$PAYLOAD" "$TARGET"

echo "SBP-070 canonical Monero app source installed: PASS"
echo "Monero remains non-selectable and was not installed into Umbrel."
echo "No blockchain runtime was modified."
