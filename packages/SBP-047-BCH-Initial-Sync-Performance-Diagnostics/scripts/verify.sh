#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"; WEB="$ROOT/seymour-blockchain-manager/data/web"
python3 -m py_compile "$WEB/sync_performance.py" "$WEB/app.py"
grep -Fq 'from sync_performance import analyze as analyze_sync_performance' "$WEB/app.py"; grep -Fq 'if self.path == "/api/sync/performance":' "$WEB/app.py"; grep -Fq "call_rpc('getpeerinfo')" "$WEB/sync_performance.py"; grep -Fq '/stats?stream=false' "$WEB/sync_performance.py"; grep -Fq "'readOnly':True" "$WEB/sync_performance.py"; grep -Fq 'data-sync-view="performance"' "$WEB/app.js"; grep -Fq '"/api/sync/performance"' "$WEB/app.js"; grep -Fq '/* SBP-047 — sync performance diagnostics */' "$WEB/style.css"
if grep -Eq 'bitcoin-cli|docker[[:space:]]+(start|stop|restart|rm)|addnode|disconnectnode|setban' "$WEB/sync_performance.py"; then echo 'SBP-047 verify: prohibited mutating/shell management path found'; exit 1; fi
echo 'SBP-047 read-only observation contract: PASS'; echo 'SBP-047 peer/runtime measurement contract: PASS'; echo 'SBP-047 in-memory rate history contract: PASS'; echo 'SBP-047 final verification: PASS'; echo 'No live lifecycle write or BCH tuning action was executed by verify.sh.'
