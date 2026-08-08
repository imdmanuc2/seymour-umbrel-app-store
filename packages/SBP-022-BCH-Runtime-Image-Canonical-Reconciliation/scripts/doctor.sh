#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fail(){ echo "SBP-022 doctor: FAIL — $*" >&2; exit 1; }
[[ -d "$ROOT/.git" ]] || fail "Umbrel app-store repository not found"
[[ "$(git -C "$ROOT" branch --show-current)" == "master" ]] || fail "Expected master branch"
for file in seymour-bch-node/docker-compose.yml seymour-bch-node/data/node/entrypoint.sh seymour-blockchain-manager/data/web/bch_rpc_probe.py; do
  [[ -f "$ROOT/$file" ]] || fail "Missing $file"
done
python3 -m py_compile "$PKG/payload/patch_bch_compose.py" "$PKG/payload/patch_healthcheck_source.py"
echo "SBP-022 doctor: PASS"
