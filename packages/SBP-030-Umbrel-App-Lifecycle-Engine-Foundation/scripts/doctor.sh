#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

[[ -d "$ROOT/.git" ]] || { echo "SBP-030 doctor: FAIL — repository not found"; exit 1; }
[[ -d "$ROOT/shared/umbrel_control" ]] || { echo "SBP-030 doctor: FAIL — Umbrel native lifecycle bridge not found"; exit 1; }

python3 -m py_compile   "$PKG/payload/shared/app_lifecycle/model.py"   "$PKG/payload/shared/app_lifecycle/engine.py"   "$PKG/payload/scripts/seymour-app-lifecycle"

echo "SBP-030 doctor: PASS"
