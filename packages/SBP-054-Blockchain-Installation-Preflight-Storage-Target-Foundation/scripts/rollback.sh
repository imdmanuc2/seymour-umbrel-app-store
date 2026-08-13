#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
LATEST="$ROOT/backups/sbp-054-latest"
[[ -f "$LATEST" ]] || { echo "SBP-054 rollback: backup pointer missing" >&2; exit 1; }
BACKUP="$(cat "$LATEST")"
rm -rf "$ROOT/shared/blockchain_install"
rm -f "$ROOT/shared/contracts/blockchain-install-preflight-v1.json" "$ROOT/tests/test_blockchain_install_preflight.py"
[[ ! -d "$BACKUP/blockchain_install" ]] || cp -a "$BACKUP/blockchain_install" "$ROOT/shared/"
[[ ! -f "$BACKUP/blockchain-install-preflight-v1.json" ]] || cp -a "$BACKUP/blockchain-install-preflight-v1.json" "$ROOT/shared/contracts/"
[[ ! -f "$BACKUP/test_blockchain_install_preflight.py" ]] || cp -a "$BACKUP/test_blockchain_install_preflight.py" "$ROOT/tests/"
echo "SBP-054 rollback: PASS"
echo "No running blockchain runtime or chain data was modified."
