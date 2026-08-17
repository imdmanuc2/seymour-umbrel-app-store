#!/usr/bin/env bash
set -euo pipefail

PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT="$(cd "$PKG/../.." && pwd)"

echo "SBP-063.3.6 doctor: checking hybrid fresh-install prerequisites"

required=(
  "$ROOT/seymour-bch-node/docker-compose.yml"
  "$ROOT/seymour-blockchain-manager/data/web/installer.py"
  "$ROOT/shared/blockchain_install/binding.py"
  "$PKG/payload/seymour-bch-node/docker-compose.yml"
  "$PKG/payload/seymour-bch-node/hooks/pre-install"
  "$PKG/payload/seymour-blockchain-manager/data/web/installer.py"
)
for path in "${required[@]}"; do
  [[ -f "$path" ]] || { echo "Missing: $path" >&2; exit 1; }
done

grep -q 'SEYMOUR_BLOCKCHAIN_LOCAL_DATA_PATH' "$PKG/payload/seymour-bch-node/docker-compose.yml"
grep -q 'SEYMOUR_BLOCKCHAIN_BLOCKS_PATH' "$PKG/payload/seymour-bch-node/docker-compose.yml"
grep -q 'seymour-bch-node-rpc' "$PKG/payload/seymour-bch-node/docker-compose.yml"
grep -q '_write_runtime_binding_config' "$PKG/payload/seymour-blockchain-manager/data/web/installer.py"
grep -q 'runtimeBindingConfig' "$PKG/payload/seymour-blockchain-manager/data/web/installer.py"

python3 -m py_compile \
  "$PKG/payload/seymour-blockchain-manager/data/web/installer.py" \
  "$PKG/payload/shared/blockchain_install/binding.py" \
  "$PKG/payload/shared/blockchain_install/runtime_binding.py"

bash -n "$PKG/payload/seymour-bch-node/hooks/pre-install"

echo "SBP-063.3.6 payload compile contract: PASS"
echo "SBP-063.3.6 hybrid compose contract: PASS"
echo "SBP-063.3.6 pre-install hook contract: PASS"
echo "SBP-063.3.6 doctor: PASS"
