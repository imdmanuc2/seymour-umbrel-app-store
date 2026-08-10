#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$ROOT/backups/sbp-036.1-$STAMP"
COMPOSE="$ROOT/seymour-blockchain-manager/docker-compose.yml"

"$PKG/scripts/doctor.sh" "$ROOT"

mkdir -p "$BACKUP/seymour-blockchain-manager"
cp -a "$COMPOSE" "$BACKUP/seymour-blockchain-manager/docker-compose.yml"

python3 - "$COMPOSE" <<'PY'
from pathlib import Path
import sys

p = Path(sys.argv[1])
s = p.read_text()

control_env = "      SEYMOUR_UMBREL_CONTROL_SCRIPT: /control/seymour-umbrel-app\n"
if control_env not in s:
    raise SystemExit("SBP-036.1 install: control environment anchor missing")

additions = []
if "      SEYMOUR_PLATFORM_ROOT: /seymour-platform\n" not in s:
    additions.append("      SEYMOUR_PLATFORM_ROOT: /seymour-platform\n")
if "      SEYMOUR_LIFECYCLE_AUDIT_PATH: /evidence/lifecycle-audit.jsonl\n" not in s:
    additions.append("      SEYMOUR_LIFECYCLE_AUDIT_PATH: /evidence/lifecycle-audit.jsonl\n")
if "      SEYMOUR_LIFECYCLE_NATIVE_EVIDENCE_PATH: /evidence/native-app-control\n" not in s:
    additions.append("      SEYMOUR_LIFECYCLE_NATIVE_EVIDENCE_PATH: /evidence/native-app-control\n")
if additions:
    s = s.replace(control_env, control_env + "".join(additions), 1)

mount = "      - /home/umbrel/seymour-umbrel-app-store-git/shared:/seymour-platform/shared:ro\n"
control_mount = "      - /home/umbrel/seymour-umbrel-app-store-git/scripts:/control:ro\n"
if mount not in s:
    if control_mount not in s:
        raise SystemExit("SBP-036.1 install: control volume anchor missing")
    s = s.replace(control_mount, control_mount + mount, 1)

p.write_text(s)
PY

python3 - "$COMPOSE" <<'PY'
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text()
required = [
    "SEYMOUR_PLATFORM_ROOT: /seymour-platform",
    "SEYMOUR_LIFECYCLE_AUDIT_PATH: /evidence/lifecycle-audit.jsonl",
    "SEYMOUR_LIFECYCLE_NATIVE_EVIDENCE_PATH: /evidence/native-app-control",
    "/home/umbrel/seymour-umbrel-app-store-git/shared:/seymour-platform/shared:ro",
]
missing=[x for x in required if x not in s]
if missing:
    raise SystemExit("SBP-036.1 install: post-write verification failed: " + ", ".join(missing))
PY

mkdir -p "$ROOT/backups"
printf '%s\n' "$BACKUP" > "$ROOT/backups/sbp-036.1-latest"

echo "Backup: $BACKUP"
echo "SBP-036.1 install: runtime wiring repair PASS"
echo "Blockchain Manager restart was NOT performed by install.sh."
echo "No live Umbrel lifecycle write action was executed."
echo
echo "NEXT: restart Blockchain Manager with the canonical native Umbrel bridge:"
echo "  cd $ROOT"
echo "  ./scripts/seymour-umbrel-app restart seymour-blockchain-manager --execute --confirm RESTART-seymour-blockchain-manager"
echo "Then run verify.sh."
