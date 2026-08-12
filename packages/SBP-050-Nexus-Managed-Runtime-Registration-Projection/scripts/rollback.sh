#!/usr/bin/env bash
set -euo pipefail
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT="$(cd "$PKG/../.." && pwd)"
BACKUP="${1:-$(find "$ROOT/backups" -maxdepth 1 -type d -name 'sbp-050-*' | sort | tail -1)}"

[[ -n "$BACKUP" && -d "$BACKUP" ]] || {
  echo "SBP-050 rollback: backup not found" >&2
  exit 1
}

cp -a "$BACKUP/shared/managed_runtime/__init__.py"   "$ROOT/shared/managed_runtime/__init__.py"

if [[ -f "$BACKUP/shared/managed_runtime/registration.py" ]]; then
  cp -a "$BACKUP/shared/managed_runtime/registration.py"     "$ROOT/shared/managed_runtime/registration.py"
else
  rm -f "$ROOT/shared/managed_runtime/registration.py"
fi

if [[ -f "$BACKUP/shared/contracts/managed-runtime-registration-v1.json" ]]; then
  cp -a "$BACKUP/shared/contracts/managed-runtime-registration-v1.json"     "$ROOT/shared/contracts/managed-runtime-registration-v1.json"
else
  rm -f "$ROOT/shared/contracts/managed-runtime-registration-v1.json"
fi

cp -a "$BACKUP/seymour-blockchain-manager/data/web/nexus_integration.py"   "$ROOT/seymour-blockchain-manager/data/web/nexus_integration.py"

echo "SBP-050 rollback: PASS"
echo "No lifecycle write, Nexus delivery, restart, or blockchain configuration action was executed."
