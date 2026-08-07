#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"; BACKUP="${2:-}"
[[ -f "$BACKUP/app.py" && -f "$BACKUP/nexus_integration.py" ]] || { echo "Invalid backup" >&2; exit 1; }
cp "$BACKUP/app.py" "$ROOT/seymour-blockchain-manager/data/web/app.py"; cp "$BACKUP/nexus_integration.py" "$ROOT/seymour-blockchain-manager/data/web/nexus_integration.py"; rm -f "$ROOT/seymour-blockchain-manager/data/web/bch_runtime_probe.py" "$ROOT/tests/test_bch_runtime_probe.py" "$ROOT/tests/test_bch_runtime_contract.py"; echo "SBP-020 rollback: PASS"
