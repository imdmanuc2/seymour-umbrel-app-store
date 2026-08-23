#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"

TARGET="/home/umbrel/umbrel/app-data/seymour-blockchain-manager/data/shared/blockchain_install"

echo "===== SBP-075.4 INSTALL ====="

mkdir -p "$TARGET"

for FILE in \
  runtime_binding.py \
  runtime_binding_materializer.py \
  runtime_binding_reconciler.py
do
  install -m 0644 \
    "shared/blockchain_install/$FILE" \
    "$TARGET/$FILE"
done

if [[ -f shared/blockchain_install/__init__.py ]]; then
  install -m 0644 \
    shared/blockchain_install/__init__.py \
    "$TARGET/__init__.py"
fi

echo "PASS: installed runtime binding projection"
