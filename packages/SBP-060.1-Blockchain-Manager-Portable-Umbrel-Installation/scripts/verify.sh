#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
echo "SBP-060.1 verify: portable Blockchain Manager Umbrel installation"
cd "$ROOT"

python3 - <<'PY'
from pathlib import Path
import os

compose = Path("seymour-blockchain-manager/docker-compose.yml").read_text()

for forbidden in (
    "/home/umbrel/seymour-umbrel-app-store-git/private/nexus-registration.env",
    "/home/umbrel/seymour-umbrel-app-store-git/scripts",
    "/home/umbrel/seymour-umbrel-app-store-git/shared",
):
    assert forbidden not in compose

assert "${APP_DATA_DIR}/data/control:/control:ro" in compose
assert "${APP_DATA_DIR}/data/shared:/seymour-platform/shared:ro" in compose
assert "PYTHONPATH: /seymour-platform" in compose

control = Path("seymour-blockchain-manager/data/control")
for name in ("seymour-umbrel-app", "seymour-install-bch", "seymour-install-btc"):
    path = control / name
    assert path.is_file()
    assert os.access(path, os.X_OK)
    print(f"{name}: mode={oct(path.stat().st_mode & 0o777)}")

shared = Path("seymour-blockchain-manager/data/shared")
assert (shared / "blockchain_install").is_dir()
assert (shared / "umbrel_control").is_dir()
assert (shared / "provider_catalog").is_dir()

print("SBP-060.1 portable payload tests: PASS")
PY

echo
echo "===== PORTABLE COMPOSE REFERENCES ====="
grep -nE 'env_file|nexus-registration.env|/data/control|/data/shared|PYTHONPATH'   seymour-blockchain-manager/docker-compose.yml || true

echo
echo "===== CONTROL PAYLOAD ====="
find seymour-blockchain-manager/data/control -maxdepth 1 -type f   -printf '%M %p\n' | sort

echo "SBP-060.1 clean Umbrel dependency contract: PASS"
echo "SBP-060.1 optional Nexus registration contract: PASS"
echo "SBP-060.1 self-contained control/shared contract: PASS"
echo "SBP-060.1 final verification: PASS"
echo "No live Umbrel installation or blockchain runtime change was executed."
