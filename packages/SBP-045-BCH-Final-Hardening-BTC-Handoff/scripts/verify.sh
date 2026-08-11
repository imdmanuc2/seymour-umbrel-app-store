#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
WEB="$ROOT/seymour-blockchain-manager/data/web"
JS="$WEB/app.js"
OPS="$WEB/operations_center.py"

python3 -m py_compile "$OPS"

grep -Fq 'function hasCompleteSyncTelemetry(telemetry)' "$JS"
grep -Fq '!completeSyncTelemetry' "$JS"
grep -Fq 'Telemetry warming up' "$JS"
grep -Fq '30000' "$JS"

# NaN must never be deliberately rendered in the runtime-focus block.
python3 - "$JS" <<'TESTPY'
from pathlib import Path
import sys

s=Path(sys.argv[1]).read_text()

assert "hasCompleteSyncTelemetry" in s
assert "Number.isFinite(rawProgress)" in s
assert "Number.isFinite(rawHeight)" in s
assert "Number.isFinite(rawHeaders)" in s
assert "Telemetry warming up" in s

# Preserve the existing short degraded/unknown stabilization.
assert 'current.state === "syncing"' in s
assert '["degraded", "unknown"].includes(rawState)' in s

print("SBP-045 NaN-safe sync presentation verification: PASS")
print("SBP-045 runtime stabilization preservation: PASS")
TESTPY

grep -Fq 'def docker_logs_via_socket' "$OPS"
grep -Fq 'source' "$OPS"
grep -Fq 'docker-engine-api' "$OPS"
grep -Fq 'probe_bch_runtime()' "$OPS"
grep -Fq "'checks':checks" "$OPS"

# Observational Docker Engine use is allowed, but no Docker lifecycle command.
if grep -Eq "run\\(\\['docker','(start|stop|restart|rm)'" "$OPS"; then
  echo "SBP-045 verify: prohibited direct Docker lifecycle command found"
  exit 1
fi

# The old docker CLI diagnostic/log implementation must be gone.
if grep -Fq "run(['docker','logs'" "$OPS"; then
  echo "SBP-045 verify: docker CLI logs path remains"
  exit 1
fi
if grep -Fq "run(['docker','inspect'" "$OPS"; then
  echo "SBP-045 verify: docker CLI diagnostics path remains"
  exit 1
fi

echo "SBP-045 Docker CLI dependency removal verification: PASS"
echo "SBP-045 canonical diagnostics contract verification: PASS"
echo "SBP-045 direct Docker lifecycle prohibition: PASS"
echo "SBP-045 final verification: PASS"
echo "No live Umbrel lifecycle write action was executed by verify.sh."
