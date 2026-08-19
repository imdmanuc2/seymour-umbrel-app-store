#!/usr/bin/env bash
set -euo pipefail

echo "SBP-068 rollback requires restoring the repository files"
echo "from Git because this package modifies source contracts only."
echo "No blockchain runtime requires rollback."
