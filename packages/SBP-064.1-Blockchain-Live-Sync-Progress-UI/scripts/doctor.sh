#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
APP="$ROOT/seymour-blockchain-manager/data/web/app.js"

echo "SBP-064.1 doctor: checking live sync UI prerequisites"

test -f "$APP"

grep -q 'async function refreshTelemetry()' "$APP"
grep -q 'fetch("/api/dashboard"' "$APP"
grep -q 'setInterval(refreshTelemetry, 5000)' "$APP"

echo "SBP-064.1 existing 5-second telemetry refresh: PASS"

grep -q 'function renderRuntimeFocus()' "$APP"
grep -q 'function progressBar(value, label)' "$APP"

echo "SBP-064.1 runtime presentation anchors: PASS"

echo "SBP-064.1 doctor: PASS"
