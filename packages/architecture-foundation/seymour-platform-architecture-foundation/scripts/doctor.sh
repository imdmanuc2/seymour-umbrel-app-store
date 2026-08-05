#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
required=(
  README.md
  docs/00-architecture-index.md
  docs/01-vision.md
  docs/02-platform-principles.md
  docs/03-product-catalog.md
  docs/04-platform-architecture.md
  docs/05-service-contracts.md
  docs/07-blockchain-platform.md
  docs/15-roadmap.md
)
for file in "${required[@]}"; do
  [[ -f "$ROOT/$file" ]] || { echo "DOCTOR FAIL: missing $file" >&2; exit 1; }
done

echo "Seymour Platform Architecture doctor: PASS"
