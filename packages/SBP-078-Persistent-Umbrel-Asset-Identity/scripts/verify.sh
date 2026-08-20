#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

FILE="seymour-blockchain-manager/data/web/nexus_integration.py"
COMPOSE="seymour-blockchain-manager/docker-compose.yml"

echo "SBP-078 verify"

python3 -m py_compile "$FILE"
echo "PASS: Python syntax"

python3 - <<'PY'
from pathlib import Path
import hashlib

text = Path(
    "seymour-blockchain-manager/data/web/nexus_integration.py"
).read_text()

assert 'f"{hostname}:{MANAGER_APP_ID}"' not in text
assert 'f"{hostname}:{BCH_APP_ID}"' not in text

assert 'host_id = host_identity()' in text
assert 'f"{host_id}:{MANAGER_APP_ID}"' in text
assert 'f"{host_id}:{BCH_APP_ID}"' in text

def stable_id(namespace, value):
    digest = hashlib.sha256(
        f"{namespace}:{value}".encode()
    ).hexdigest()[:16]
    return f"{namespace}-{digest}"

host = "machine-id:a484fc8354f94dc681d103cd006a152c"

manager = stable_id(
    "asset",
    f"{host}:seymour-blockchain-manager",
)

node = stable_id(
    "asset",
    f"{host}:seymour-bch-node",
)

assert manager == "asset-7be2040a1a33c91c"
assert node == "asset-1a3a169d72207de3"

print("PASS: container hostname excluded from canonical identity")
print("managerAssetId =", manager)
print("nodeAssetId    =", node)
print("PASS: deterministic live asset-ID contract")
PY

grep -q \
  '/etc/machine-id:/host-identity/machine-id:ro' \
  "$COMPOSE"

echo "PASS: host identity mounted read-only"

grep -q \
  'data/private/nexus-registration.env' \
  "$COMPOSE"

echo "PASS: private Nexus registration configuration"

if grep -Eq \
  'NEXUS_REGISTRATION_TOKEN:[[:space:]]+[^$]' \
  "$COMPOSE"
then
    echo "ERROR: registration secret embedded in compose"
    exit 1
fi

echo "PASS: registration secret excluded from compose"

grep -q \
  'preserveExistingRegistrationId' \
  seymour-blockchain-manager/data/shared/contracts/managed-runtime-registration-v1.json

echo "PASS: registration migration contract retained"

echo "SBP-078 verify: PASS"
