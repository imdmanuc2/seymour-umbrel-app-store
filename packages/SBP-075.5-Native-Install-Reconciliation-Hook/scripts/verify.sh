#!/usr/bin/env bash
set -euo pipefail

PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT="$(cd "$PKG/../.." && pwd)"

ROOT_CONTROL="$ROOT/shared/umbrel_control"
MANAGER_CONTROL="$ROOT/seymour-blockchain-manager/data/shared/umbrel_control"

INSTALLED_CONTROL="/home/umbrel/umbrel/app-data/seymour-blockchain-manager/data/shared/umbrel_control"

echo "===== SBP-075.5 VERIFY ====="

cmp -s \
  "$PKG/payload/shared/umbrel_control/bridge.py" \
  "$ROOT_CONTROL/bridge.py"

cmp -s \
  "$PKG/payload/shared/umbrel_control/http_client.py" \
  "$ROOT_CONTROL/http_client.py"

echo "PASS: host control projection matches package"

cmp -s \
  "$ROOT_CONTROL/bridge.py" \
  "$MANAGER_CONTROL/bridge.py"

cmp -s \
  "$ROOT_CONTROL/http_client.py" \
  "$MANAGER_CONTROL/http_client.py"

echo "PASS: Manager source projection matches host"

cmp -s \
  "$ROOT_CONTROL/bridge.py" \
  "$INSTALLED_CONTROL/bridge.py"

cmp -s \
  "$ROOT_CONTROL/http_client.py" \
  "$INSTALLED_CONTROL/http_client.py"

echo "PASS: installed Manager projection matches host"

echo
echo "===== HOST CONTROL IMPORT ====="

cd "$ROOT"

PYTHONDONTWRITEBYTECODE=1 \
python3 - <<'PY'
import sys
from pathlib import Path

repo = Path.cwd()

sys.path.insert(
    0,
    str(repo / "shared"),
)

from umbrel_control import UmbrelAppControlBridge
from umbrel_control.http_client import UmbrelHttpClient

print("bridge =", UmbrelAppControlBridge)
print("http =", UmbrelHttpClient)
print("PASS: host control imports")
PY

echo
echo "===== READ-ONLY NATIVE STATE ====="

STATE="$(
  ./scripts/seymour-umbrel-app \
    state \
    seymour-monero-node
)"

printf '%s\n' "$STATE"

python3 - "$STATE" <<'PY'
import json
import sys

payload = json.loads(sys.argv[1])

assert payload["success"] is True

result = payload.get("result")

assert isinstance(result, dict)
assert result.get("state") in {
    "ready",
    "running",
}

print("PASS: host lifecycle command operational")
PY

echo
echo "===== NO-OP BINDING RECONCILIATION ====="

PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH="$ROOT" \
python3 - <<'PY'
from pathlib import Path

from shared.blockchain_install.runtime_binding_reconciler import (
    reconcile_installed_runtime_binding,
)

result = reconcile_installed_runtime_binding(
    data_directory=Path(
        "/home/umbrel/umbrel"
    ),
    binding_path=Path(
        "/home/umbrel/umbrel/app-data/"
        "seymour-blockchain-manager/data/evidence/"
        "runtime-bindings/seymour-monero-node.env"
    ),
)

print(result)

assert result["changed"] is False

print("PASS: existing Monero compose requires no restart")
PY

echo
echo "===== LIVE MONERO NON-INTERFERENCE ====="

sudo docker inspect \
  seymour-monero-node_node_1 \
  --format 'status={{.State.Status}} health={{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}} restarts={{.RestartCount}}'

echo "SBP-075.5 VERIFY PASS"
