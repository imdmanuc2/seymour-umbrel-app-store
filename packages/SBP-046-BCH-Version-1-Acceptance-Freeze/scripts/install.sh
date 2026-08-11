#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$ROOT/backups/sbp-046-$STAMP"

"$PKG/scripts/doctor.sh" "$ROOT"

mkdir -p "$BACKUP"
cat > "$BACKUP/README.txt" <<EOF
SBP-046 is a read-only acceptance/freeze package.
No application files were changed by install.sh.
Created: $STAMP
EOF

printf '%s\n' "$BACKUP" > "$ROOT/backups/sbp-046-latest"

echo "Backup marker: $BACKUP"
echo "SBP-046 install: PASS"
echo "No repository/runtime files were modified."
echo "No lifecycle write was executed."
