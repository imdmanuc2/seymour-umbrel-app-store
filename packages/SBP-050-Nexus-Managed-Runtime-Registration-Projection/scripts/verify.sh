#!/usr/bin/env bash
set -euo pipefail
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT="$(cd "$PKG/../.." && pwd)"
cd "$ROOT"

python3 -m py_compile   shared/managed_runtime/__init__.py   shared/managed_runtime/registration.py   seymour-blockchain-manager/data/web/nexus_integration.py

python3 - <<'PY'
import json
from pathlib import Path
c=json.loads(Path("shared/contracts/managed-runtime-registration-v1.json").read_text())
assert c["contract"]=="seymour.managed-runtime-registration"
assert c["sourceContract"]=="seymour.managed-runtime/1.0"
assert c["preserveExistingRegistrationId"] is True
assert c["preserveExistingDeliveryIdempotency"] is True
assert c["duplicateRegistrationPath"] is False
assert c["duplicateLifecycleExecutionPath"] is False
assert c["directDockerLifecycle"] is False
assert c["lifecycleWrites"] is False
PY

python3 - <<'PY'
from shared.managed_runtime.registration import attach_managed_runtime_projection

original = {
    "registrationId": "registration-stable-123",
    "host": {"id": "host-1"},
    "assets": [{
        "assetId": "asset-bch",
        "name": "Bitcoin Cash",
        "providerId": "bitcoin-cash-mainnet",
        "runtimeState": "syncing",
        "telemetry": {
            "installed": True,
            "running": True,
            "runtimeState": "syncing",
            "runtimeStateReason": "IBD active",
            "runtimeRpcReachable": True,
            "runtimeRpcHealthy": True,
            "runtimeInitialBlockDownload": True,
            "runtimeVerificationProgress": 0.48,
            "peers": 8,
        },
    }],
}

projected = attach_managed_runtime_projection(original)
assert projected["registrationId"] == "registration-stable-123"
assert projected["assets"] == original["assets"]
assert projected["managedRuntimeContract"] == "seymour.managed-runtime-registration/1.0"
assert len(projected["managedRuntimes"]) == 1
runtime = projected["managedRuntimes"][0]
assert runtime["contract"] == "seymour.managed-runtime"
assert runtime["identity"]["providerId"] == "bitcoin-cash-mainnet"
assert runtime["state"]["state"] == "syncing"
assert runtime["state"]["rpcReachable"] is True
assert runtime["state"]["rpcHealthy"] is True
assert runtime["state"]["initialBlockDownload"] is True
assert runtime["state"]["verificationProgress"] == 0.48
assert runtime["telemetry"]["peers"] == 8
PY

python3 - <<'PY'
from pathlib import Path
text=Path("seymour-blockchain-manager/data/web/nexus_integration.py").read_text()
assert "# SBP-050 — canonical managed runtime registration projection" in text
assert "_sbp050_registration_payload = registration_payload" in text
assert "attach_managed_runtime_projection(payload)" in text
PY

if grep -RniE   'docker[[:space:]]+(start|stop|restart|rm)|subprocess.*docker|os\.system.*docker'   shared/managed_runtime/registration.py; then
  echo "SBP-050 verify: FAIL: direct Docker lifecycle pattern detected" >&2
  exit 1
fi

if grep -nE 'urlopen|requests\.(post|put|patch)|httpx\.(post|put|patch)'   shared/managed_runtime/registration.py; then
  echo "SBP-050 verify: FAIL: duplicate delivery path detected" >&2
  exit 1
fi

echo "SBP-050 managed runtime registration contract verification: PASS"
echo "SBP-050 stable registration identity preservation verification: PASS"
echo "SBP-050 legacy asset compatibility verification: PASS"
echo "SBP-050 canonical managed runtime projection verification: PASS"
echo "SBP-050 duplicate registration delivery prohibition: PASS"
echo "SBP-050 duplicate lifecycle execution prohibition: PASS"
echo "SBP-050 direct Docker lifecycle prohibition: PASS"
echo "SBP-050 final verification: PASS"
echo "No live Nexus delivery, lifecycle write, restart, or blockchain configuration action was executed by verify.sh."
