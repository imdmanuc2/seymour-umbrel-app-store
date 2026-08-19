#!/usr/bin/env bash
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
INSTALLER="$REPO/seymour-blockchain-manager/data/web/installer.py"
CATALOG="$REPO/shared/provider_catalog/providers.v1.json"

echo "SBP-069 doctor: checking provider-neutral installation prerequisites"
test -f "$INSTALLER"
test -f "$CATALOG"
python3 -m py_compile "$INSTALLER"
python3 -m py_compile "$(dirname "${BASH_SOURCE[0]}")/patch.py"
grep -q '"providerId": "monero-mainnet"' "$CATALOG"
grep -q '"authentication": "none"' "$CATALOG"
echo "SBP-069 provider runtime metadata prerequisite: PASS"
echo "SBP-069 doctor: PASS"
