#!/usr/bin/env bash
set -euo pipefail
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
"$PKG/scripts/doctor.sh"
echo "SBP-066 install: acceptance package requires no runtime mutation."
echo "SBP-066 install: PASS"
echo "No blockchain runtime was installed, stopped, started, restarted, recreated, updated, or uninstalled."
echo "NEXT: run verify.sh."
