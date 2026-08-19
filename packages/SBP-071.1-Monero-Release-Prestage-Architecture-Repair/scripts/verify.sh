#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
WF="$REPO/.github/workflows/seymour-monero-node-multiarch.yml"

echo "SBP-071.1 verify: Monero prestage architecture repair"

grep -q 'Do not execute the staged binary here.' "$WF"

if grep -A2 -B2 'runtime-images/monero/staged/monerod' "$WF" \
  | grep -q -- '--version'; then
  echo "ERROR: host-side staged binary execution remains"
  exit 1
fi

echo "SBP-071.1 host-execution prohibition contract: PASS"

grep -q 'docker/setup-qemu-action@v3' "$WF"
grep -q 'docker buildx build' "$WF"
grep -q 'docker run' "$WF"
grep -q -- '--platform "${{ matrix.platform }}"' "$WF"
grep -q -- '--version' "$WF"

echo "SBP-071.1 QEMU/architecture smoke-test contract: PASS"

grep -q 'monero-linux-x64-v0.18.5.1.tar.bz2' "$WF"
grep -q '22a7dda7b0cb699fdd6b7674c3b4a4465b337cc98a54983523b759e1e7cc9958' "$WF"
grep -q 'monero-linux-armv8-v0.18.5.1.tar.bz2' "$WF"
grep -q 'c0caf042cb7c7b760f5ad6be188084b59352440b32990a78b8051497b9398dbc' "$WF"

echo "SBP-071.1 official release integrity contract preserved: PASS"

BTC_NODE="$(sudo docker ps -a --filter 'label=com.docker.compose.project=seymour-bitcoin-node' --filter 'label=com.docker.compose.service=node' --format '{{.Names}}' | head -1)"
BCH_NODE="$(sudo docker ps -a --filter 'label=com.docker.compose.project=seymour-bch-node' --filter 'label=com.docker.compose.service=node' --format '{{.Names}}' | head -1)"

test -n "$BTC_NODE"
test -n "$BCH_NODE"

sudo docker inspect "$BTC_NODE" --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}} {{.RestartCount}}' | grep -q '^running healthy 0$'
sudo docker inspect "$BCH_NODE" --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}} {{.RestartCount}}' | grep -q '^running healthy 0$'

echo "SBP-071.1 BTC/BCH safety contract: PASS"
echo "SBP-071.1 final verification: PASS"
echo "No blockchain runtime was modified."
