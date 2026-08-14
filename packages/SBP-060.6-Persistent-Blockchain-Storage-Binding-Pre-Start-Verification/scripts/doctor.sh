#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
echo "SBP-060.6 doctor: checking persistent storage binding prerequisites"
test -f "$ROOT/seymour-blockchain-manager/data/web/installer.py"
test -d "$ROOT/shared/blockchain_install"
grep -q 'build_binding_plan' "$ROOT/seymour-blockchain-manager/data/web/installer.py"
echo "SBP-060.6 doctor: provider-neutral binding plan anchor PASS"
echo "SBP-060.6 doctor: shared blockchain install foundation PASS"
echo "SBP-060.6 doctor: PASS"
