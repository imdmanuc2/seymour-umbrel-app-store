#!/usr/bin/env bash
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
CATALOG="$REPO/shared/provider_catalog/providers.v1.json"
WEB="$REPO/seymour-blockchain-manager/data/catalog/providers.v1.json"
SHARED="$REPO/seymour-blockchain-manager/data/shared/provider_catalog/providers.v1.json"
COMPOSE="$REPO/seymour-monero-node/docker-compose.yml"
INSTALLER="$REPO/seymour-blockchain-manager/data/web/installer.py"
IMAGE="ghcr.io/imdmanuc2/seymour-monero-node:0.18.5.1"

echo "SBP-072 verify: Monero image acceptance and provider promotion"

python3 - "$CATALOG" "$IMAGE" <<'PY'
import json,sys
payload=json.load(open(sys.argv[1]))
xmr=next(p for p in payload["providers"] if p["providerId"]=="monero-mainnet")
assert xmr["nodeVersion"]=="0.18.5.1"
assert xmr["productionImage"]==sys.argv[2]
assert xmr["runtime"]["appId"]=="seymour-monero-node"
assert xmr["runtime"]["rpc"]["port"]==18081
assert xmr["runtime"]["p2p"]["port"]==18080
assert xmr["selectable"] is False
print(f"SBP-072 provider artifact: PASS availability={xmr.get('availability')} selectable={xmr.get('selectable')}")
PY

cmp -s "$CATALOG" "$WEB"
cmp -s "$CATALOG" "$SHARED"
echo "SBP-072 catalog synchronization contract: PASS"

grep -Fq "$IMAGE" "$COMPOSE"
echo "SBP-072 compose/catalog image alignment contract: PASS"

PYTHONPATH="$REPO" python3 - "$INSTALLER" "$CATALOG" <<'PY'
from pathlib import Path
import importlib.util, os, sys
installer_path=Path(sys.argv[1]); catalog_path=Path(sys.argv[2])
sys.path.insert(0,str(installer_path.parent))
os.environ["PROVIDER_CATALOG_PATH"]=str(catalog_path)
spec=importlib.util.spec_from_file_location("sbp072_installer",installer_path)
m=importlib.util.module_from_spec(spec); sys.modules[spec.name]=m; spec.loader.exec_module(m)
runtime=m.provider_runtime("monero-mainnet")
assert runtime.get("installAdapterEnabled") is False
print("SBP-072 Monero install-adapter prohibition contract: PASS")
PY

timeout 60s sudo docker image inspect "$IMAGE" >/dev/null
HOST="$(uname -m)"
ARCH="$(timeout 60s sudo docker image inspect "$IMAGE" --format '{{.Architecture}}')"
case "$HOST" in aarch64|arm64) EXPECTED=arm64;; x86_64|amd64) EXPECTED=amd64;; *) echo "ERROR: unsupported host arch $HOST"; exit 1;; esac
test "$ARCH" = "$EXPECTED"
echo "SBP-072 local image architecture contract: PASS ($ARCH)"

VERSION="$(timeout 90s sudo docker run --rm "$IMAGE" --version)"
printf '%s\n' "$VERSION"
printf '%s\n' "$VERSION" | grep -q 'v0.18.5.1-release'
echo "SBP-072 Monero runtime version contract: PASS"

if timeout 15s sudo docker ps -a --filter 'label=com.docker.compose.project=seymour-monero-node' --format '{{.Names}}' | grep -q .; then
  echo "ERROR: Monero runtime unexpectedly exists"; exit 1
fi
echo "SBP-072 no-live-Monero-runtime contract: PASS"

BTC="$(timeout 15s sudo docker ps -a --filter 'label=com.docker.compose.project=seymour-bitcoin-node' --filter 'label=com.docker.compose.service=node' --format '{{.Names}}' | head -1)"
BCH="$(timeout 15s sudo docker ps -a --filter 'label=com.docker.compose.project=seymour-bch-node' --filter 'label=com.docker.compose.service=node' --format '{{.Names}}' | head -1)"
timeout 15s sudo docker inspect "$BTC" --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}} {{.RestartCount}}' | grep -q '^running healthy 0$'
timeout 15s sudo docker inspect "$BCH" --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}} {{.RestartCount}}' | grep -q '^running healthy 0$'
echo "SBP-072 BTC/BCH safety contract: PASS"

echo "SBP-072 final Monero image acceptance/provider promotion: PASS"
echo "Monero remains non-selectable and uninstalled."
echo "No blockchain runtime was modified."
