#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

FILE="seymour-blockchain-manager/data/web/nexus_integration.py"
COMPOSE="seymour-blockchain-manager/docker-compose.yml"

echo "SBP-078 doctor"

test -f "$FILE"
test -f "$COMPOSE"
test -s /etc/machine-id

python3 -m py_compile "$FILE"

grep -q 'SEYMOUR_HOST_MACHINE_ID_PATH' "$COMPOSE"
grep -q '/etc/machine-id:/host-identity/machine-id:ro' "$COMPOSE"
grep -q 'data/private/nexus-registration.env' "$COMPOSE"

echo "PASS: Python syntax"
echo "PASS: host machine identity source"
echo "PASS: private Nexus registration environment"
echo "SBP-078 doctor: PASS"
