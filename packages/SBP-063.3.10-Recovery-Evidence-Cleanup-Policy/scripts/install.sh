#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DIR/_common.sh"
EXECUTE=false
CONFIRM=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --execute) EXECUTE=true; shift ;;
    --confirm) CONFIRM="${2:-}"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done
"$DIR/doctor.sh"
mkdir -p "$EVIDENCE_DIR" 2>/dev/null || sudo mkdir -p "$EVIDENCE_DIR"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
PRE="$EVIDENCE_DIR/${RECOVERY_ID}-${STAMP}-pre.json"
POST="$EVIDENCE_DIR/${RECOVERY_ID}-${STAMP}-post.json"
LOCAL_SIZE="$(sudo du -sb "$LOCAL_RECOVERY" | awk '{print $1}')"
REMOTE_SIZE="$(sudo du -sb "$REMOTE_RECOVERY" | awk '{print $1}')"
BLOCK_SRC="$(live_blocks_source)"
write_json() {
  local path="$1" phase="$2" local_exists="$3" remote_exists="$4"
  local payload
  payload="$(cat <<JSON
{
  \"contract\": \"seymour.recovery-cleanup\",
  \"version\": \"1.0\",
  \"recoveryId\": \"$RECOVERY_ID\",
  \"phase\": \"$phase\",
  \"confirmation\": \"$CONFIRMATION\",
  \"localRecovery\": \"$LOCAL_RECOVERY\",
  \"remoteRecovery\": \"$REMOTE_RECOVERY\",
  \"localBytesBefore\": $LOCAL_SIZE,
  \"remoteBytesBefore\": $REMOTE_SIZE,
  \"localExists\": $local_exists,
  \"remoteExists\": $remote_exists,
  \"liveBlocksSource\": \"$BLOCK_SRC\"
}
JSON
)"
  printf '%s\n' "$payload" | sudo tee "$path" >/dev/null
  sudo test -s "$path"
}
write_json "$PRE" "pre-cleanup" true true
echo "SBP-063.3.10 evidence pre-write: PASS"
if [[ "$EXECUTE" != true ]]; then
  echo "SBP-063.3.10 install: plan mode only"
  echo "Required confirmation: $CONFIRMATION"
  exit 0
fi
if [[ "$CONFIRM" != "$CONFIRMATION" ]]; then
  echo "ERROR: confirmation mismatch" >&2
  echo "Expected: $CONFIRMATION" >&2
  exit 1
fi
require_runtime_safety
sudo rm -rf -- "$LOCAL_RECOVERY" "$REMOTE_RECOVERY"
test ! -e "$LOCAL_RECOVERY"
test ! -e "$REMOTE_RECOVERY"
write_json "$POST" "post-cleanup" false false
echo "SBP-063.3.10 guarded recovery cleanup: PASS"
echo "Evidence:"
echo "  $PRE"
echo "  $POST"
echo "No blockchain runtime was stopped, restarted, recreated, or uninstalled."
