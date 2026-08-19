#!/usr/bin/env bash
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
INSTALLER="$REPO/seymour-blockchain-manager/data/web/installer.py"
INSTALLED="/home/umbrel/umbrel/app-data/seymour-blockchain-manager/data/web/installer.py"
CATALOG="$REPO/shared/provider_catalog/providers.v1.json"

echo "SBP-069 verify: provider-neutral installation contract"
python3 -m py_compile "$INSTALLER"

grep -q 'INSTALL_ADAPTERS = {' "$INSTALLER"
grep -q 'def _runtime_contract' "$INSTALLER"
grep -q 'def _rpc_authentication' "$INSTALLER"
grep -q 'rpcAuthentication' "$INSTALLER"
echo "SBP-069 provider runtime helper contract: PASS"

if grep -q '"rpc": {"port": 8332, "available": _port_available(8332)}' "$INSTALLER"; then
  echo "ERROR: fixed Bitcoin RPC preflight port remains"
  exit 1
fi
if grep -q '"p2p": {"port": 8333, "available": _port_available(8333)}' "$INSTALLER"; then
  echo "ERROR: fixed Bitcoin P2P preflight port remains"
  exit 1
fi
echo "SBP-069 fixed-port prohibition contract: PASS"

PYTHONPATH="$REPO" python3 - "$INSTALLER" "$CATALOG" <<'PY'
from pathlib import Path
import importlib.util
import os
import sys

installer_path = Path(sys.argv[1])
catalog_path = Path(sys.argv[2])

sys.path.insert(0, str(installer_path.parent))
os.environ["PROVIDER_CATALOG_PATH"] = str(catalog_path)

spec = importlib.util.spec_from_file_location("sbp069_installer", installer_path)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = module
spec.loader.exec_module(module)

btc = module._provider("bitcoin-mainnet")
bch = module._provider("bitcoin-cash-mainnet")
xmr = module._provider("monero-mainnet")

assert module._runtime_port(module._rpc_contract(btc), "RPC") == 8332
assert module._rpc_authentication(btc) == "username-password"
assert module._runtime_port(module._rpc_contract(bch), "RPC") == 8332
assert module._rpc_authentication(bch) == "username-password"
assert module._runtime_port(module._rpc_contract(xmr), "RPC") == 18081
assert module._runtime_port(module._p2p_contract(xmr), "P2P") == 18080
assert module._rpc_authentication(xmr) == "none"

xmr_runtime = module.provider_runtime("monero-mainnet")
assert xmr_runtime["appId"] == "seymour-monero-node"
assert xmr_runtime["installAdapterEnabled"] is False
assert xmr_runtime["selectable"] is False

xmr_req = module.InstallRequest(
    provider_id="monero-mainnet",
    app_id="seymour-monero-node",
    node_name="Seymour Monero Node",
    rpc_user="",
    rpc_password="",
    rpc_port=18081,
    p2p_port=18080,
    storage_target_id="synthetic",
    confirmation="INSTALL-seymour-monero-node",
)
module.validate_request(xmr_req)

btc_req = module.InstallRequest(
    provider_id="bitcoin-mainnet",
    app_id="seymour-bitcoin-node",
    node_name="Seymour Bitcoin Node",
    rpc_user="",
    rpc_password="",
    rpc_port=8332,
    p2p_port=8333,
    storage_target_id="synthetic",
    confirmation="INSTALL-seymour-bitcoin-node",
)
try:
    module.validate_request(btc_req)
except ValueError as exc:
    assert "RPC user is required" in str(exc)
else:
    raise AssertionError("BTC credential validation unexpectedly passed")

print("SBP-069 BTC/BCH authentication contract: PASS")
print("SBP-069 Monero no-auth request contract: PASS")
print("SBP-069 Monero execution remains disabled: PASS")
PY

if sudo test -f "$INSTALLED"; then
  SRC="$(sha256sum "$INSTALLER" | awk '{print $1}')"
  LIVE="$(sudo sha256sum "$INSTALLED" | awk '{print $1}')"
  test "$SRC" = "$LIVE"
  echo "SBP-069 deployed source checksum contract: PASS"
fi

python3 - "$CATALOG" <<'PY'
import json, sys
payload=json.load(open(sys.argv[1]))
xmr=next(p for p in payload["providers"] if p["providerId"]=="monero-mainnet")
assert xmr["availability"]=="planned"
assert xmr["selectable"] is False
assert xmr["productionImage"] is None
print("SBP-069 Monero non-selectable safety contract: PASS")
PY

BTC_NODE="$(sudo docker ps -a --filter 'label=com.docker.compose.project=seymour-bitcoin-node' --filter 'label=com.docker.compose.service=node' --format '{{.Names}}' | head -1)"
BCH_NODE="$(sudo docker ps -a --filter 'label=com.docker.compose.project=seymour-bch-node' --filter 'label=com.docker.compose.service=node' --format '{{.Names}}' | head -1)"
test -n "$BTC_NODE"
test -n "$BCH_NODE"

sudo docker inspect "$BTC_NODE" --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}} {{.RestartCount}}' | grep -q '^running healthy 0$'
sudo docker inspect "$BCH_NODE" --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}} {{.RestartCount}}' | grep -q '^running healthy 0$'

echo "SBP-069 BTC/BCH runtime safety contract: PASS"
echo "SBP-069 final provider-neutral installation contract: PASS"
echo "No blockchain runtime was modified."
