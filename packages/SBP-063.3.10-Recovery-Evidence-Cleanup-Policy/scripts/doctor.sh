#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DIR/_common.sh"
echo "SBP-063.3.10 doctor: checking recovery cleanup prerequisites"
require_runtime_safety
echo "SBP-063.3.10 runtime safety contract: PASS"
test -d "$LOCAL_RECOVERY"
test -d "$REMOTE_RECOVERY"
echo "SBP-063.3.10 recovery dataset inventory: PASS"
echo "SBP-063.3.10 required confirmation: $CONFIRMATION"
echo "SBP-063.3.10 doctor: PASS"
