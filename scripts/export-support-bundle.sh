#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(
  cd "$(dirname "${BASH_SOURCE[0]}")/.."
  pwd
)"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUTPUT="${1:-$HOME/seymour-support-bundle-$STAMP.tar.gz}"
STAGING="$(mktemp -d)"

cleanup() {
  rm -rf "$STAGING"
}

trap cleanup EXIT

mkdir -p \
  "$STAGING/runtime-evidence" \
  "$STAGING/system"

if [[ -d "$REPO_ROOT/runtime-evidence" ]]; then
  cp -a \
    "$REPO_ROOT/runtime-evidence/." \
    "$STAGING/runtime-evidence/"
fi

git -C "$REPO_ROOT" status \
  > "$STAGING/system/git-status.txt"

git -C "$REPO_ROOT" log \
  -10 \
  --oneline \
  > "$STAGING/system/git-log.txt"

{
  echo "Generated: $(date -u --iso-8601=seconds)"
  echo "Repository: $REPO_ROOT"
  echo "Host: $(hostname)"
  echo "Kernel: $(uname -a)"
} > "$STAGING/system/summary.txt"

sudo docker ps -a \
  > "$STAGING/system/docker-ps.txt" \
  2>&1 || true

sudo journalctl \
  -u umbrel.service \
  --since "2 hours ago" \
  --no-pager \
  > "$STAGING/system/umbrel-journal.txt" \
  2>&1 || true

tar -C "$STAGING" \
  -czf "$OUTPUT" \
  .

chmod 600 "$OUTPUT"

echo "Support bundle created:"
echo "$OUTPUT"
