#!/usr/bin/env bash
set -euo pipefail
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
"$PKG/scripts/doctor.sh"
echo "SBP-067 install: acceptance package requires no runtime mutation."
echo "SBP-067 install: PASS"
echo "No blockchain runtime was stopped, started, restarted, updated, recreated, repaired, or uninstalled."
echo "NEXT: run verify.sh."
