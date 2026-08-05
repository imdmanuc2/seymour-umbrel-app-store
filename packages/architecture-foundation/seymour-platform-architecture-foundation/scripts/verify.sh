#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
"$ROOT/scripts/doctor.sh"

grep -q 'Finish before expanding' "$ROOT/docs/02-platform-principles.md"
grep -q 'Bitcoin Core' "$ROOT/docs/07-blockchain-platform.md"
grep -q 'Bitcoin Cash Node' "$ROOT/docs/07-blockchain-platform.md"
grep -q 'Recommended setup' "$ROOT/docs/12-user-experience.md"
grep -q 'service contracts' "$ROOT/docs/13-dependency-resolution.md"

echo "Seymour Platform Architecture verification: PASS"
