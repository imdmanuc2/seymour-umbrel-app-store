#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
MARKER="$ROOT/backups/sbp-048-latest"
APPDATA="/home/umbrel/umbrel/app-data/seymour-bch-node"

[[ -f "$MARKER" ]] || { echo "SBP-048 rollback: backup marker missing"; exit 1; }
BACKUP="$(cat "$MARKER")"

for rel in \
  seymour-bch-node/data/status/provisioning.py \
  seymour-bch-node/data/node/entrypoint.sh \
  seymour-bch-node/data/status/templates/provision.html
do
  cp -a "$BACKUP/$rel" "$ROOT/$rel"
done

if [[ -f "$BACKUP/bitcoin.conf.live-before" ]]; then
  cp -a "$BACKUP/bitcoin.conf.live-before" "$APPDATA/data/generated/bitcoin.conf"
fi

cp -a "$ROOT/seymour-bch-node/data/status/provisioning.py" "$APPDATA/data/status/provisioning.py"
cp -a "$ROOT/seymour-bch-node/data/status/templates/provision.html" "$APPDATA/data/status/templates/provision.html"
cp -a "$ROOT/seymour-bch-node/data/node/entrypoint.sh" "$APPDATA/data/node/entrypoint.sh"

echo "SBP-048 rollback: txindex policy restored"
echo "A native BCH restart is required after rollback."
echo "SBP-048 rollback: PASS"
