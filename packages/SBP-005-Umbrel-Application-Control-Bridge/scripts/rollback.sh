#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
BACKUP="${2:-}"

[[ -d "$BACKUP" ]] || {
  echo "Invalid backup: $BACKUP" >&2
  exit 1
}

for name in shared scripts docs; do
  rm -rf "$REPO/$name"

  if [[ -e "$BACKUP/$name" ]]; then
    cp -a "$BACKUP/$name" "$REPO/"
  fi
done

echo "SBP-005 rollback: PASS"
