#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
"$ROOT/scripts/doctor.sh"
echo "Architecture repository is self-contained; no host installation is required."
echo "Seymour Platform Architecture install: PASS"
