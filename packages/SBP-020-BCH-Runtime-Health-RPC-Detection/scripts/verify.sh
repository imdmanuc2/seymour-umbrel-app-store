#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
export PYTHONPATH="$ROOT/seymour-blockchain-manager/data/web:$ROOT${PYTHONPATH:+:$PYTHONPATH}"
python3 "$ROOT/tests/test_bch_runtime_probe.py"
python3 "$ROOT/tests/test_bch_runtime_contract.py"
python3 -m py_compile "$ROOT/seymour-blockchain-manager/data/web/bch_runtime_probe.py" "$ROOT/seymour-blockchain-manager/data/web/nexus_integration.py" "$ROOT/seymour-blockchain-manager/data/web/app.py"
echo "SBP-020 direct Docker socket verification: PASS"
echo "SBP-020 installed/running classification verification: PASS"
echo "SBP-020 RPC degradation separation verification: PASS"
echo "SBP-020 BCH runtime API verification: PASS"
echo "SBP-020 Nexus payload normalization verification: PASS"
echo "SBP-020 final verification: PASS"
