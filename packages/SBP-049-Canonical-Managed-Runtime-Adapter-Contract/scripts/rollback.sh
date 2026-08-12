#!/usr/bin/env bash
set -euo pipefail
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT="$(cd "$PKG/../.." && pwd)"
BACKUP="${1:-$(find "$ROOT/backups" -maxdepth 1 -type d -name 'sbp-049-*' | sort | tail -1)}"
[[ -n "$BACKUP" && -d "$BACKUP" ]] || { echo "SBP-049 rollback: backup not found" >&2; exit 1; }
rm -rf "$ROOT/shared/managed_runtime"
[[ ! -d "$BACKUP/shared/managed_runtime" ]] || cp -a "$BACKUP/shared/managed_runtime" "$ROOT/shared/"
cp -a "$BACKUP/shared/contracts/app-lifecycle-v1.json" "$ROOT/shared/contracts/app-lifecycle-v1.json"
rm -f "$ROOT/shared/contracts/managed-runtime-adapter-v1.json"
echo "SBP-049 rollback: PASS"
