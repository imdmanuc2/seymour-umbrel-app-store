#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"

WF="$REPO/.github/workflows/seymour-monero-node-multiarch.yml"
DOCKERFILE="$REPO/runtime-images/monero/Dockerfile"
CATALOG="$REPO/shared/provider_catalog/providers.v1.json"
COMPOSE="$REPO/seymour-monero-node/docker-compose.yml"

echo "SBP-071 verify: Monero multi-arch runtime image foundation"

test -f "$WF"
test -f "$DOCKERFILE"

grep -q 'docker buildx build' "$WF"
grep -q 'docker buildx imagetools create' "$WF"
grep -q 'publish-manifest:' "$WF"
grep -q 'linux/amd64' "$WF"
grep -q 'linux/arm64' "$WF"
echo "SBP-071 direct Buildx multi-arch contract: PASS"

grep -q '22a7dda7b0cb699fdd6b7674c3b4a4465b337cc98a54983523b759e1e7cc9958' "$WF"
grep -q 'c0caf042cb7c7b760f5ad6be188084b59352440b32990a78b8051497b9398dbc' "$WF"
grep -q 'sha256sum -c' "$WF"
echo "SBP-071 official release checksum contract: PASS"

grep -q 'monero-linux-x64-v0.18.5.1.tar.bz2' "$WF"
grep -q 'monero-linux-armv8-v0.18.5.1.tar.bz2' "$WF"
grep -q 'downloads.getmonero.org/cli' "$WF"
echo "SBP-071 official release download contract: PASS"

grep -q 'COPY staged/monerod /usr/local/bin/monerod' "$DOCKERFILE"
grep -q '/usr/local/bin/monerod --version' "$DOCKERFILE"
grep -q 'ENTRYPOINT \["/usr/local/bin/monerod"\]' "$DOCKERFILE"
grep -q 'EXPOSE 18080 18081' "$DOCKERFILE"
echo "SBP-071 runtime image contract: PASS"

grep -Fq 'ghcr.io/imdmanuc2/seymour-monero-node:0.18.5.1' "$COMPOSE"
echo "SBP-071 compose image alignment contract: PASS"

python3 - "$CATALOG" <<'PY'
import json
import sys

payload = json.load(open(sys.argv[1]))
xmr = next(
    p for p in payload["providers"]
    if p["providerId"] == "monero-mainnet"
)

assert xmr["nodeVersion"] == "0.18.5.1"
assert xmr["supportedArchitectures"] == ["amd64", "arm64"]
assert xmr["availability"] == "planned"
assert xmr["selectable"] is False
assert xmr["productionImage"] is None

print("SBP-071 Monero activation safety contract: PASS")
PY

if sudo docker ps -a --format '{{.Names}}' | grep -q '^seymour-monero-node'; then
  echo "ERROR: Monero runtime unexpectedly exists"
  exit 1
fi
echo "SBP-071 no-live-Monero-runtime contract: PASS"

BTC_NODE="$(
  sudo docker ps -a \
    --filter 'label=com.docker.compose.project=seymour-bitcoin-node' \
    --filter 'label=com.docker.compose.service=node' \
    --format '{{.Names}}' | head -1
)"
BCH_NODE="$(
  sudo docker ps -a \
    --filter 'label=com.docker.compose.project=seymour-bch-node' \
    --filter 'label=com.docker.compose.service=node' \
    --format '{{.Names}}' | head -1
)"

test -n "$BTC_NODE"
test -n "$BCH_NODE"

sudo docker inspect "$BTC_NODE" \
  --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}} {{.RestartCount}}' \
  | grep -q '^running healthy 0$'

sudo docker inspect "$BCH_NODE" \
  --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}} {{.RestartCount}}' \
  | grep -q '^running healthy 0$'

echo "SBP-071 BTC/BCH safety contract: PASS"
echo "SBP-071 final Monero multi-arch image foundation: PASS"
echo "No blockchain runtime was modified."
