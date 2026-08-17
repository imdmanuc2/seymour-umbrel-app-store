#!/usr/bin/env bash
set -euo pipefail

PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT="$(cd "$PKG/../.." && pwd)"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$ROOT/backups/sbp-063.3.6-$TS"
MANAGER_DATA="/home/umbrel/umbrel/app-data/seymour-blockchain-manager/data"
BCH_DATA="/home/umbrel/umbrel/app-data/seymour-bch-node"

"$PKG/scripts/doctor.sh"
mkdir -p "$BACKUP"

backup_one() {
  local source="$1"
  local rel="$2"
  if [[ -e "$source" ]]; then
    mkdir -p "$BACKUP/$(dirname "$rel")"
    cp -a "$source" "$BACKUP/$rel"
  fi
}

backup_one "$ROOT/seymour-bch-node/docker-compose.yml" "repo/seymour-bch-node/docker-compose.yml"
backup_one "$ROOT/seymour-bch-node/hooks/pre-install" "repo/seymour-bch-node/hooks/pre-install"
backup_one "$ROOT/seymour-blockchain-manager/data/web/installer.py" "repo/seymour-blockchain-manager/data/web/installer.py"
backup_one "$ROOT/shared/blockchain_install/binding.py" "repo/shared/blockchain_install/binding.py"
backup_one "$ROOT/shared/blockchain_install/runtime_binding.py" "repo/shared/blockchain_install/runtime_binding.py"
backup_one "$MANAGER_DATA/web/installer.py" "installed-manager/web/installer.py"
backup_one "$MANAGER_DATA/shared/blockchain_install/binding.py" "installed-manager/shared/blockchain_install/binding.py"
backup_one "$MANAGER_DATA/shared/blockchain_install/runtime_binding.py" "installed-manager/shared/blockchain_install/runtime_binding.py"
backup_one "$BCH_DATA/hooks/pre-install" "installed-bch/hooks/pre-install"

mkdir -p "$ROOT/seymour-bch-node/hooks"
cp -a "$PKG/payload/seymour-bch-node/docker-compose.yml" "$ROOT/seymour-bch-node/docker-compose.yml"
cp -a "$PKG/payload/seymour-bch-node/hooks/pre-install" "$ROOT/seymour-bch-node/hooks/pre-install"
chmod +x "$ROOT/seymour-bch-node/hooks/pre-install"

cp -a "$PKG/payload/seymour-blockchain-manager/data/web/installer.py" "$ROOT/seymour-blockchain-manager/data/web/installer.py"
cp -a "$PKG/payload/shared/blockchain_install/binding.py" "$ROOT/shared/blockchain_install/binding.py"
cp -a "$PKG/payload/shared/blockchain_install/runtime_binding.py" "$ROOT/shared/blockchain_install/runtime_binding.py"

echo "SBP-063.3.6 repository source synchronized: PASS"

if [[ -d "$MANAGER_DATA" ]]; then
  mkdir -p "$MANAGER_DATA/web" "$MANAGER_DATA/shared/blockchain_install"
  cp -a "$PKG/payload/seymour-blockchain-manager/data/web/installer.py" "$MANAGER_DATA/web/installer.py"
  cp -a "$PKG/payload/shared/blockchain_install/binding.py" "$MANAGER_DATA/shared/blockchain_install/binding.py"
  cp -a "$PKG/payload/shared/blockchain_install/runtime_binding.py" "$MANAGER_DATA/shared/blockchain_install/runtime_binding.py"
  echo "SBP-063.3.6 installed Blockchain Manager source synchronized: PASS"
fi

# Safe to stage the hook in existing app-data; do not touch the proven live compose.
if [[ -d "$BCH_DATA" ]]; then
  mkdir -p "$BCH_DATA/hooks"
  cp -a "$PKG/payload/seymour-bch-node/hooks/pre-install" "$BCH_DATA/hooks/pre-install"
  chmod +x "$BCH_DATA/hooks/pre-install"
  echo "SBP-063.3.6 installed BCH hook synchronized: PASS"
fi

cat > "$BACKUP/manifest.txt" <<MANIFEST
package=SBP-063.3.6
created=$TS
repository=$ROOT
manager_data=$MANAGER_DATA
bch_data=$BCH_DATA
MANIFEST

echo "Backup: $BACKUP"
echo "SBP-063.3.6 install: PASS"
echo "No blockchain runtime was installed, stopped, restarted, recreated, or uninstalled."
echo "The currently installed BCH docker-compose.yml was deliberately left untouched."
echo "NEXT: run verify.sh, then restart Blockchain Manager only to load the new installer code."
