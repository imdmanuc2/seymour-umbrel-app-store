#!/usr/bin/env bash
set -euo pipefail
REPO="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fail(){ echo "SBP-019 doctor: FAIL — $*" >&2; exit 1; }
[[ -d "$REPO/.git" ]] || fail "repository missing"
[[ "$(git -C "$REPO" branch --show-current)" == "master" ]] || fail "expected master"
for f in seymour-blockchain-manager/data/web/app.py seymour-blockchain-manager/data/web/nexus_delivery.py seymour-blockchain-manager/data/web/nexus_integration.py seymour-blockchain-manager/docker-compose.yml; do [[ -f "$REPO/$f" ]] || fail "missing $f"; done
python3 -m py_compile "$ROOT/payload/nexus_scheduler.py" "$ROOT/payload/patch_app.py" "$ROOT/payload/patch_compose.py"
echo "SBP-019 doctor: PASS"
