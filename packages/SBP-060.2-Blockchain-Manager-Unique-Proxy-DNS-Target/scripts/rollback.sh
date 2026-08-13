#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
LATEST="$ROOT/backups/sbp-060.2-latest"
test -f "$LATEST"
BACKUP="$(cat "$LATEST")"
cp -a "$BACKUP/seymour-blockchain-manager/docker-compose.yml" "$ROOT/seymour-blockchain-manager/docker-compose.yml"
rm -f "$ROOT/tests/test_blockchain_manager_unique_proxy_dns.py"
echo "SBP-060.2 rollback: PASS"
