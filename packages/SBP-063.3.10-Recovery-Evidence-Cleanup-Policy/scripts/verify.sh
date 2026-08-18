#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DIR/_common.sh"
echo "SBP-063.3.10 verify: recovery evidence and cleanup policy"
require_runtime_safety
echo "SBP-063.3.10 runtime safety contract: PASS"
if [[ -e "$LOCAL_RECOVERY" || -e "$REMOTE_RECOVERY" ]]; then
  echo "SBP-063.3.10 cleanup status: recovery data still retained"
  echo "Run install.sh --execute --confirm $CONFIRMATION when ready."
  exit 0
fi
echo "SBP-063.3.10 recovery datasets removed: PASS"
if sudo find "$EVIDENCE_DIR" -maxdepth 1 -type f -name "${RECOVERY_ID}-*-post.json" -print -quit 2>/dev/null | grep -q .; then
  echo "SBP-063.3.10 post-cleanup evidence contract: PASS"
else
  echo "ERROR: post-cleanup evidence not found" >&2
  exit 1
fi
echo "SBP-063.3.10 final verification: PASS"
