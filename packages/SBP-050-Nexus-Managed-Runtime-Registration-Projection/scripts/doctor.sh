#!/usr/bin/env bash
set -euo pipefail
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT="$(cd "$PKG/../.." && pwd)"
cd "$ROOT"

test -f shared/managed_runtime/models.py
test -f shared/contracts/managed-runtime-adapter-v1.json
test -f seymour-blockchain-manager/data/web/nexus_integration.py
test -f seymour-blockchain-manager/data/web/nexus_delivery.py
test -f seymour-blockchain-manager/data/web/nexus_scheduler.py

grep -q 'def registration_payload' seymour-blockchain-manager/data/web/nexus_integration.py
grep -q 'NEXUS_REGISTRATION_URL' seymour-blockchain-manager/data/web/nexus_delivery.py

echo "SBP-050 doctor: existing Nexus registration/delivery anchors PASS"
echo "SBP-050 doctor: SBP-049 managed runtime anchors PASS"
echo "SBP-050 doctor: PASS"
