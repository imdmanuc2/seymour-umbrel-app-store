#!/usr/bin/env bash
set -euo pipefail

PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT="$(cd "$PKG/../.." && pwd)"
BACKUP="${1:-}"
if [[ -z "$BACKUP" ]]; then
  BACKUP="$(find "$ROOT/backups" -maxdepth 1 -type d -name 'sbp-063.3.6-*' -print 2>/dev/null | sort | tail -1)"
fi
[[ -n "$BACKUP" && -d "$BACKUP" ]] || { echo "SBP-063.3.6 rollback: backup not found" >&2; exit 1; }

restore_one() {
  local saved="$1"
  local target="$2"
  if [[ -e "$saved" ]]; then
    mkdir -p "$(dirname "$target")"
    cp -a "$saved" "$target"
  fi
}

restore_one "$BACKUP/repo/seymour-bch-node/docker-compose.yml" "$ROOT/seymour-bch-node/docker-compose.yml"
restore_one "$BACKUP/repo/seymour-bch-node/hooks/pre-install" "$ROOT/seymour-bch-node/hooks/pre-install"
restore_one "$BACKUP/repo/seymour-blockchain-manager/data/web/installer.py" "$ROOT/seymour-blockchain-manager/data/web/installer.py"
restore_one "$BACKUP/repo/shared/blockchain_install/binding.py" "$ROOT/shared/blockchain_install/binding.py"
restore_one "$BACKUP/repo/shared/blockchain_install/runtime_binding.py" "$ROOT/shared/blockchain_install/runtime_binding.py"
restore_one "$BACKUP/installed-manager/web/installer.py" "/home/umbrel/umbrel/app-data/seymour-blockchain-manager/data/web/installer.py"
restore_one "$BACKUP/installed-manager/shared/blockchain_install/binding.py" "/home/umbrel/umbrel/app-data/seymour-blockchain-manager/data/shared/blockchain_install/binding.py"
restore_one "$BACKUP/installed-manager/shared/blockchain_install/runtime_binding.py" "/home/umbrel/umbrel/app-data/seymour-blockchain-manager/data/shared/blockchain_install/runtime_binding.py"
restore_one "$BACKUP/installed-bch/hooks/pre-install" "/home/umbrel/umbrel/app-data/seymour-bch-node/hooks/pre-install"

echo "SBP-063.3.6 rollback: PASS"
echo "Restored from: $BACKUP"
echo "No blockchain runtime was restarted by rollback."
