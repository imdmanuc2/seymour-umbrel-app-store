#!/usr/bin/env bash
set -euo pipefail
RECOVERY_ID="20260818-000411"
BCH_APP="seymour-bch-node"
BTC_APP="seymour-bitcoin-node"
LOCAL_RECOVERY="/home/umbrel/umbrel/app-data/seymour-bch-node/data/node/recovery-${RECOVERY_ID}"
REMOTE_RECOVERY="/mnt/seymour-storage/bitcoin-cash-mainnet/recovery-${RECOVERY_ID}"
REMOTE_BLOCKS="/mnt/seymour-storage/bitcoin-cash-mainnet/blocks"
EVIDENCE_DIR="/home/umbrel/umbrel/app-data/seymour-blockchain-manager/data/evidence/recovery-cleanup"
CONFIRMATION="DELETE-BCH-RECOVERY-${RECOVERY_ID}"

bch_state() {
  sudo docker inspect "${BCH_APP}_node_1" --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}} {{.RestartCount}}'
}

btc_state() {
  sudo docker inspect "${BTC_APP}_node_1" --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}} {{.RestartCount}}'
}

live_blocks_source() {
  sudo docker inspect "${BCH_APP}_node_1" --format '{{range .Mounts}}{{if eq .Destination "/data/blocks"}}{{.Source}}{{end}}{{end}}'
}

require_runtime_safety() {
  local bs bh br ts th tr src
  read -r bs bh br <<<"$(bch_state)"
  read -r ts th tr <<<"$(btc_state)"
  src="$(live_blocks_source)"
  test "$bs" = "running"
  test "$bh" = "healthy"
  test "$br" = "0"
  test "$ts" = "running"
  test "$th" = "healthy"
  test "$tr" = "0"
  test "$src" = "$REMOTE_BLOCKS"
}
