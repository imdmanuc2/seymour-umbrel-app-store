#!/usr/bin/env bash
set -euo pipefail

PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT="$(cd "$PKG/../.." && pwd)"
MANAGER_DATA="/home/umbrel/umbrel/app-data/seymour-blockchain-manager/data"

echo "SBP-063.3.6 verify: hybrid storage fresh-install integration"

python3 -m py_compile \
  "$ROOT/seymour-blockchain-manager/data/web/installer.py" \
  "$ROOT/shared/blockchain_install/binding.py" \
  "$ROOT/shared/blockchain_install/runtime_binding.py"
echo "SBP-063.3.6 Python compile contract: PASS"

grep -q 'SEYMOUR_BLOCKCHAIN_LOCAL_DATA_PATH' "$ROOT/seymour-bch-node/docker-compose.yml"
grep -q 'SEYMOUR_BLOCKCHAIN_BLOCKS_PATH' "$ROOT/seymour-bch-node/docker-compose.yml"
grep -q ':/data/blocks' "$ROOT/seymour-bch-node/docker-compose.yml"
grep -q ':/node-data/blocks' "$ROOT/seymour-bch-node/docker-compose.yml"
grep -q 'seymour-bch-node-rpc' "$ROOT/seymour-bch-node/docker-compose.yml"
echo "SBP-063.3.6 portable hybrid compose contract: PASS"

grep -q 'runtime-bindings/seymour-bch-node.env' "$ROOT/seymour-bch-node/hooks/pre-install"
grep -q 'expected 4 storage anchors' "$ROOT/seymour-bch-node/hooks/pre-install"
echo "SBP-063.3.6 host pre-install hook contract: PASS"

python3 - "$ROOT/seymour-blockchain-manager/data/web/installer.py" <<'PY'
from pathlib import Path
import sys
text = Path(sys.argv[1]).read_text()
write = text.index('_write_runtime_binding_config(')
call = text.index('binding_config = _write_runtime_binding_config(')
install = text.index('completed = subprocess.run(', call)
if not (write < call < install):
    raise SystemExit('runtime binding config is not written before native install')
if 'persist_runtime_binding(' in text:
    raise SystemExit('post-install compose mutation path is still present')
print('SBP-063.3.6 pre-install ordering contract: PASS')
PY

# Regression-test the hook without touching any live runtime.
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
UMBREL="$TMP/umbrel"
APP="$UMBREL/app-data/seymour-bch-node"
MGR="$UMBREL/app-data/seymour-blockchain-manager/data/evidence/runtime-bindings"
mkdir -p "$APP/hooks" "$MGR"
cp "$ROOT/seymour-bch-node/docker-compose.yml" "$APP/docker-compose.yml"
cp "$ROOT/seymour-bch-node/hooks/pre-install" "$APP/hooks/pre-install"
cat > "$MGR/seymour-bch-node.env" <<ENV
SEYMOUR_BLOCKCHAIN_LOCAL_DATA_PATH=/tmp/seymour-local-bch
SEYMOUR_BLOCKCHAIN_BLOCKS_PATH=/tmp/seymour-remote-bch/blocks
ENV
APP_DATA_DIR="$APP" UMBREL_ROOT="$UMBREL" "$APP/hooks/pre-install" >/dev/null
grep -q '/tmp/seymour-local-bch:/data' "$APP/docker-compose.yml"
grep -q '/tmp/seymour-remote-bch/blocks:/data/blocks' "$APP/docker-compose.yml"
grep -q '/tmp/seymour-local-bch:/node-data' "$APP/docker-compose.yml"
grep -q '/tmp/seymour-remote-bch/blocks:/node-data/blocks' "$APP/docker-compose.yml"
echo "SBP-063.3.6 isolated fresh-install hook regression: PASS"

if [[ -d "$MANAGER_DATA" ]]; then
  cmp "$ROOT/seymour-blockchain-manager/data/web/installer.py" "$MANAGER_DATA/web/installer.py"
  cmp "$ROOT/shared/blockchain_install/binding.py" "$MANAGER_DATA/shared/blockchain_install/binding.py"
  cmp "$ROOT/shared/blockchain_install/runtime_binding.py" "$MANAGER_DATA/shared/blockchain_install/runtime_binding.py"
  echo "SBP-063.3.6 deployed Manager checksum contract: PASS"
fi

# Read-only live safety observations. Do not fail verification if sudo is unavailable.
if command -v docker >/dev/null 2>&1 && sudo -n docker version >/dev/null 2>&1; then
  if sudo -n docker inspect seymour-bitcoin-node_node_1 >/dev/null 2>&1; then
    sudo -n docker inspect seymour-bitcoin-node_node_1 \
      --format 'BTC safety: status={{.State.Status}} restarts={{.RestartCount}}'
  fi
  if sudo -n docker inspect seymour-bch-node_node_1 >/dev/null 2>&1; then
    sudo -n docker inspect seymour-bch-node_node_1 \
      --format '{{range .Mounts}}{{if eq .Destination "/data"}}{{printf "BCH /data: %s\n" .Source}}{{end}}{{if eq .Destination "/data/blocks"}}{{printf "BCH /data/blocks: %s\n" .Source}}{{end}}{{end}}'
  fi
fi

echo "SBP-063.3.6 final verification: PASS"
echo "No live blockchain runtime was modified."
