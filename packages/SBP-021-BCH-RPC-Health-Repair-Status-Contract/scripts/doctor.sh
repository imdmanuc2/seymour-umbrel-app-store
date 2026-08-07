#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fail(){ echo "SBP-021 doctor: FAIL — $*" >&2; exit 1; }
[[ -d "$ROOT/.git" ]] || fail "Umbrel app-store repository not found"
[[ "$(git -C "$ROOT" branch --show-current)" == "master" ]] || fail "Expected master branch"
for f in seymour-blockchain-manager/data/web/app.py seymour-blockchain-manager/data/web/bch_runtime_probe.py seymour-blockchain-manager/docker-compose.yml; do [[ -f "$ROOT/$f" ]] || fail "Missing $f"; done
python3 -m py_compile "$PKG/payload/bch_rpc_probe.py" "$PKG/payload/patch_runtime_probe.py" "$PKG/payload/patch_app.py" "$PKG/payload/patch_compose.py"
echo "SBP-021 doctor: PASS"
