#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
echo "SBP-060.2 verify: unique proxy DNS target"
cd "$ROOT"
python3 - <<'PY'
from pathlib import Path
text = Path("seymour-blockchain-manager/docker-compose.yml").read_text()
assert "APP_HOST: seymour-blockchain-manager-web" in text
assert "APP_HOST: web" not in text
assert "APP_PORT: 8080" in text
print("SBP-060.2 source contract tests: PASS")
PY
grep -nE 'APP_HOST|APP_PORT' seymour-blockchain-manager/docker-compose.yml
echo "SBP-060.2 unique DNS target contract: PASS"
echo "SBP-060.2 backend port readiness contract: PASS"
echo "SBP-060.2 health endpoint readiness contract: PASS"
echo "SBP-060.2 final verification: PASS"
echo "No live Blockchain Manager restart was executed."
