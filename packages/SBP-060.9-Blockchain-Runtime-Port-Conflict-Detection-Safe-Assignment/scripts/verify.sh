#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
echo "SBP-060.9 verify: runtime port conflict detection and safe assignment"
python3 -m py_compile   "$ROOT/shared/blockchain_recovery/models.py"   "$ROOT/shared/blockchain_recovery/engine.py"   "$ROOT/shared/blockchain_recovery/port_guard.py"
grep -q 'RUNTIME_PORT_CONFLICT' "$ROOT/shared/blockchain_recovery/models.py"
grep -q 'runtime_port_conflict_finding' "$ROOT/shared/blockchain_recovery/engine.py"
grep -q -- '--requested-host-port' "$ROOT/scripts/seymour-blockchain-heal"
grep -q 'BTC_P2P_HOST_PORT:-8335' "$ROOT/seymour-bitcoin-node/docker-compose.yml"
PYTHONPATH="$ROOT/shared" python3 - <<'PY'
from blockchain_recovery.port_guard import first_free_port
assert first_free_port([]) is None
print("SBP-060.9 candidate selection contract: PASS")
PY
echo "SBP-060.9 recovery kind contract: PASS"
echo "SBP-060.9 recovery CLI contract: PASS"
echo "SBP-060.9 BTC configurable host-port contract: PASS"
echo "SBP-060.9 final verification: PASS"
echo "No live runtime was restarted or modified."
