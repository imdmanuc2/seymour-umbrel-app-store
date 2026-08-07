#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fail(){ echo "SBP-020 doctor: FAIL — $*" >&2; exit 1; }
[[ -d "$ROOT/.git" ]] || fail "repo missing"
[[ "$(git -C "$ROOT" branch --show-current)" == master ]] || fail "expected master"
for f in seymour-blockchain-manager/data/web/app.py seymour-blockchain-manager/data/web/nexus_integration.py seymour-blockchain-manager/docker-compose.yml; do [[ -f "$ROOT/$f" ]] || fail "Missing $f"; done
grep -q BCH_NODE_CONTAINER "$ROOT/seymour-blockchain-manager/docker-compose.yml" || fail "BCH_NODE_CONTAINER missing"
grep -q '/var/run/docker.sock:/var/run/docker.sock:ro' "$ROOT/seymour-blockchain-manager/docker-compose.yml" || fail "Docker socket mount missing"
python3 -m py_compile "$PKG/payload/bch_runtime_probe.py" "$PKG/payload/patch_app.py" "$PKG/payload/patch_nexus_integration.py"
echo "SBP-020 doctor: PASS"
