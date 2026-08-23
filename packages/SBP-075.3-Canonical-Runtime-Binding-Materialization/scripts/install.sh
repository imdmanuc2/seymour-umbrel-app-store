#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PKG="$ROOT/packages/SBP-075.3-Canonical-Runtime-Binding-Materialization"

"$PKG/scripts/doctor.sh"

install -D -m 0644 \
  "$PKG/payload/shared/blockchain_install/runtime_binding_materializer.py" \
  "$ROOT/shared/blockchain_install/runtime_binding_materializer.py"

install -D -m 0644 \
  "$PKG/payload/seymour-blockchain-manager/data/shared/blockchain_install/runtime_binding_materializer.py" \
  "$ROOT/seymour-blockchain-manager/data/shared/blockchain_install/runtime_binding_materializer.py"

echo "PASS: canonical runtime binding materializer installed"
echo "SBP-075.3 INSTALL PASS"
