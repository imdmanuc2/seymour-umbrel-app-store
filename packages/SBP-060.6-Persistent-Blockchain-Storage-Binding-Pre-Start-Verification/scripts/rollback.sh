#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
rm -f \
  "$ROOT/shared/blockchain_install/runtime_binding.py" \
  "$ROOT/shared/blockchain_install/prestart_guard.py" \
  "$ROOT/tests/test_runtime_binding.py"
echo "SBP-060.6 rollback: PASS"
echo "No blockchain runtime or blockchain data was modified."
