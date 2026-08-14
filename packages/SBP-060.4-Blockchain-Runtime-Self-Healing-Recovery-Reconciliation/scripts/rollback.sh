#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
rm -rf "$ROOT/shared/blockchain_recovery"
rm -f "$ROOT/shared/contracts/blockchain-runtime-recovery-v1.json" "$ROOT/scripts/seymour-blockchain-heal" "$ROOT/tests/test_blockchain_runtime_recovery.py"
echo "SBP-060.4 rollback: PASS"
