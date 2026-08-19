#!/usr/bin/env bash
set -euo pipefail

echo "SBP-073 rollback is backup-driven."
echo "Restore installer.py and provider catalogs from the desired backups/sbp-073-* directory."
echo "Remove scripts/seymour-install-monero if reverting the adapter."
echo "Rollback does not stop, start, restart, or uninstall blockchain runtimes."
