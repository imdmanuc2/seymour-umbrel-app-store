#!/usr/bin/env bash
set -euo pipefail

PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT="$(cd "$PKG/../.." && pwd)"

SOURCE="$PKG/payload/seymour-blockchain-manager/data/web/nexus_integration.py"
REPO_TARGET="$ROOT/seymour-blockchain-manager/data/web/nexus_integration.py"
INSTALLED_TARGET="/home/umbrel/umbrel/app-data/seymour-blockchain-manager/data/web/nexus_integration.py"

echo "===== SBP-075.5.1 VERIFY ====="

cmp -s "$SOURCE" "$REPO_TARGET"
echo "PASS: repository projection matches package"

cmp -s "$SOURCE" "$INSTALLED_TARGET"
echo "PASS: installed projection matches package"

PYTHONDONTWRITEBYTECODE=1 python3 - "$SOURCE" "$REPO_TARGET" "$INSTALLED_TARGET" <<'PY'
from pathlib import Path
import sys

for filename in sys.argv[1:]:
    path = Path(filename)
    compile(path.read_text(), str(path), "exec")

print("PASS: Python syntax")
PY

echo "SBP-075.5.1 VERIFY PASS"
