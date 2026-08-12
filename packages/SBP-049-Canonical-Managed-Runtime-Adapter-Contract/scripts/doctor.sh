#!/usr/bin/env bash
set -euo pipefail
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT="$(cd "$PKG/../.." && pwd)"
cd "$ROOT"
test -f shared/runtime_state/service.py
test -f shared/app_lifecycle/model.py
test -f shared/app_lifecycle/engine.py
test -f shared/umbrel_runtime/runtime.py
test -f shared/contracts/app-lifecycle-v1.json
echo "SBP-049 doctor: existing runtime/lifecycle architecture anchors PASS"
echo "SBP-049 doctor: PASS"
