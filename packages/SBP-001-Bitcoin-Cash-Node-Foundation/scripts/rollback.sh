#!/usr/bin/env bash
set -euo pipefail
REPO="${1:-/home/umbrel/seymour-umbrel-app-store-git}";BACKUP="${2:-}"
[[ -d "$BACKUP/seymour-bch-node" ]]||{ echo "Invalid backup: $BACKUP" >&2; exit 1; }
rm -rf "$REPO/seymour-bch-node";cp -a "$BACKUP/seymour-bch-node" "$REPO/";echo "SBP-001 rollback: PASS"
