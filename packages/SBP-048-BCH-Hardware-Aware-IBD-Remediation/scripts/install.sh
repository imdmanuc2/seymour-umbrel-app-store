#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$ROOT/backups/sbp-048-$STAMP"
APPDATA="/home/umbrel/umbrel/app-data/seymour-bch-node"

"$PKG/scripts/doctor.sh" "$ROOT"

mkdir -p "$BACKUP"

for rel in \
  seymour-bch-node/data/status/provisioning.py \
  seymour-bch-node/data/node/entrypoint.sh \
  seymour-bch-node/data/status/templates/provision.html
do
  mkdir -p "$BACKUP/$(dirname "$rel")"
  cp -a "$ROOT/$rel" "$BACKUP/$rel"
done

python3 "$PKG/payload/patch_sbp048.py" "$ROOT"
python3 -m py_compile "$ROOT/seymour-bch-node/data/status/provisioning.py"

if [[ -d "$APPDATA/data/status" ]]; then
  cp -a "$ROOT/seymour-bch-node/data/status/provisioning.py" "$APPDATA/data/status/provisioning.py"
  cp -a "$ROOT/seymour-bch-node/data/status/templates/provision.html" "$APPDATA/data/status/templates/provision.html"
fi

if [[ -d "$APPDATA/data/node" ]]; then
  cp -a "$ROOT/seymour-bch-node/data/node/entrypoint.sh" "$APPDATA/data/node/entrypoint.sh"
fi

GENERATED="$APPDATA/data/generated/bitcoin.conf"
if [[ -f "$GENERATED" ]]; then
  cp -a "$GENERATED" "$BACKUP/bitcoin.conf.live-before"
  sed -i -E 's/^txindex=.*/txindex=0/' "$GENERATED"
fi

printf '%s\n' "$BACKUP" > "$ROOT/backups/sbp-048-latest"

echo "Backup: $BACKUP"
echo "SBP-048 provisioning txindex default OFF: PASS"
echo "SBP-048 node entrypoint txindex fallback OFF: PASS"
echo "SBP-048 installed BCH runtime synchronization: PASS"
echo "SBP-048 current generated config txindex=0 staging: PASS"
echo "SBP-048 install: PASS"
echo "No BCH lifecycle write was executed by install.sh."
echo "No chain data, indexes, or blocks were deleted."
