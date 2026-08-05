#!/usr/bin/env bash
set -euo pipefail
REPO="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)";BACKUP="$REPO/backups/sbp-001-$STAMP"
"$ROOT/scripts/doctor.sh" "$REPO"
mkdir -p "$BACKUP";cp -a "$REPO/seymour-bch-node" "$BACKUP/";rm -rf "$REPO/seymour-bch-node";cp -a "$ROOT/payload/seymour-bch-node" "$REPO/"
mkdir -p "$REPO/docs";cp -a "$ROOT/payload/docs/." "$REPO/docs/"
echo "Backup: $BACKUP";echo "SBP-001 install: PASS";echo "No app, container, blockchain sync, firewall, or host changes were performed."
