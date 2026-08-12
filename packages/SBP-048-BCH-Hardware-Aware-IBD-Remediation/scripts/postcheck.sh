#!/usr/bin/env bash
set -euo pipefail

echo "===== LIVE CONFIG ====="
sudo docker exec -i seymour-bch-node_node_1 \
  grep '^txindex=' /generated/bitcoin.conf || true

echo
echo "===== INDEX STATUS ====="
sudo docker exec -i seymour-bch-node_node_1 \
  bitcoin-cli -conf=/generated/bitcoin.conf getindexinfo 2>&1 || true

echo
echo "===== CHAIN STATE ====="
sudo docker exec -i seymour-bch-node_node_1 \
  bitcoin-cli -conf=/generated/bitcoin.conf getblockchaininfo \
  | grep -E '"blocks"|"headers"|"verificationprogress"|"initialblockdownload"'

echo
echo "===== MEMORY ====="
free -h

echo
echo "===== IOWAIT SAMPLE ====="
vmstat 1 10

echo
echo "===== CONTAINER STATS ====="
sudo docker stats \
  --no-stream \
  --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.BlockIO}}\t{{.NetIO}}" \
  seymour-bch-node_node_1

echo
echo "===== 10-MINUTE THROUGHPUT SAMPLE ====="
for i in {1..10}; do
  echo "===== $(date) ====="
  sudo docker exec -i seymour-bch-node_node_1 \
    bitcoin-cli -conf=/generated/bitcoin.conf getblockchaininfo \
    | grep -E '"blocks"|"headers"|"verificationprogress"|"initialblockdownload"'
  sudo docker exec -i seymour-bch-node_node_1 \
    bitcoin-cli -conf=/generated/bitcoin.conf getnetworkinfo \
    | grep '"connections"'
  sleep 60
done
