#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
echo "SBP-060.7 doctor: checking runtime start guard prerequisites"
test -f "$ROOT/shared/umbrel_control/bridge.py"
test -f "$ROOT/shared/blockchain_install/runtime_binding.py"
grep -q 'operation.mode = "execute"' "$ROOT/shared/umbrel_control/bridge.py"
echo "SBP-060.7 doctor: native start bridge anchor PASS"
echo "SBP-060.7 doctor: persistent binding dependency PASS"
echo "SBP-060.7 doctor: PASS"
