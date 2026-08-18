#!/usr/bin/env bash
set -euo pipefail
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
"$PKG/scripts/doctor.sh"
echo "SBP-063.3.9 install: acceptance package requires no runtime mutation."
echo "SBP-063.3.9 install: PASS"
echo "No blockchain runtime was installed, stopped, restarted, recreated, or uninstalled."
echo "NEXT: run verify.sh."
