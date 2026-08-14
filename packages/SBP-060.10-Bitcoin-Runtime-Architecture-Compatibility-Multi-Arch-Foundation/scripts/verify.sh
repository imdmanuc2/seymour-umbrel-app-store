#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"

echo "SBP-060.10 verify: Bitcoin runtime architecture compatibility"

python3 -m py_compile   "$ROOT/shared/bitcoin_managed_runtime/architecture.py"   "$ROOT/shared/blockchain_recovery/image_architecture.py"   "$ROOT/shared/blockchain_recovery/models.py"   "$ROOT/shared/blockchain_recovery/engine.py"

grep -q 'RUNTIME_IMAGE_ARCHITECTURE_MISMATCH'   "$ROOT/shared/blockchain_recovery/models.py"

grep -q 'runtime_image_architecture_finding'   "$ROOT/shared/blockchain_recovery/engine.py"

grep -q -- '--runtime-image'   "$ROOT/scripts/seymour-blockchain-heal"

grep -q 'SBP-060.10 architecture guard'   "$ROOT/scripts/seymour-bitcoin-managed-runtime"

PYTHONPATH="$ROOT/shared" python3 - <<'PY'
from runtime_architecture import normalize_architecture
assert normalize_architecture("x86_64") == "amd64"
assert normalize_architecture("amd64") == "amd64"
assert normalize_architecture("aarch64") == "arm64"
assert normalize_architecture("arm64") == "arm64"
print("SBP-060.10 architecture normalization contract: PASS")
PY

echo "SBP-060.10 recovery kind contract: PASS"
echo "SBP-060.10 recovery CLI contract: PASS"
echo "SBP-060.10 guarded Bitcoin wrapper contract: PASS"
echo "SBP-060.10 final verification: PASS"
echo "No live runtime was restarted or modified."
