#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$ROOT/backups/sbp-037-$STAMP"

"$PKG/scripts/doctor.sh" "$ROOT"

mkdir -p "$BACKUP/shared/app_lifecycle" "$BACKUP/seymour-blockchain-manager/data/web"
for f in engine.py model.py executor.py __init__.py; do
  cp -a "$ROOT/shared/app_lifecycle/$f" "$BACKUP/shared/app_lifecycle/$f"
done
cp -a "$ROOT/seymour-blockchain-manager/data/web/lifecycle_routes.py"   "$BACKUP/seymour-blockchain-manager/data/web/lifecycle_routes.py"

cp -a "$PKG/payload/shared/app_lifecycle/runtime_state.py"   "$ROOT/shared/app_lifecycle/runtime_state.py"

python3 - "$ROOT" <<'PATCHPY'
from pathlib import Path
import sys

root = Path(sys.argv[1])
model = root / "shared/app_lifecycle/model.py"
engine = root / "shared/app_lifecycle/engine.py"
executor = root / "shared/app_lifecycle/executor.py"
init = root / "shared/app_lifecycle/__init__.py"
routes = root / "seymour-blockchain-manager/data/web/lifecycle_routes.py"

s = model.read_text()
old = '    "not-installed", "installing", "stopped", "starting", "running",\n    "restarting", "updating", "uninstalling", "degraded", "error", "unknown",\n'
new = '    "not-installed", "installing", "stopped", "starting", "syncing", "running",\n    "restarting", "updating", "uninstalling", "degraded", "offline", "error", "unknown",\n'
if old in s:
    s = s.replace(old, new, 1)
elif '"syncing"' not in s or '"offline"' not in s:
    raise SystemExit("SBP-037 install: model state anchor not found")
model.write_text(s)

s = engine.read_text()
if '    "syncing": {"stop", "restart"},\n' not in s:
    anchor = '    "running": {"stop", "restart", "update", "uninstall"},\n'
    if anchor not in s:
        raise SystemExit("SBP-037 install: running policy anchor not found")
    s = s.replace(anchor, '    "syncing": {"stop", "restart"},\n' + anchor, 1)
if '    "offline": {"start"},\n' not in s:
    anchor = '    "error": {"start", "stop", "restart", "update", "uninstall"},\n'
    if anchor not in s:
        raise SystemExit("SBP-037 install: error policy anchor not found")
    s = s.replace(anchor, '    "offline": {"start"},\n' + anchor, 1)
engine.write_text(s)

s = executor.read_text()
old_ctor = '''    def __init__(self, bridge: Any, engine: AppLifecycleEngine | None = None) -> None:
        self.bridge = bridge
        self.engine = engine or AppLifecycleEngine()
'''
new_ctor = '''    def __init__(
        self,
        bridge: Any,
        engine: AppLifecycleEngine | None = None,
        state_provider: Any | None = None,
    ) -> None:
        self.bridge = bridge
        self.engine = engine or AppLifecycleEngine()
        self.state_provider = state_provider
'''
if old_ctor in s:
    s = s.replace(old_ctor, new_ctor, 1)
elif "self.state_provider = state_provider" not in s:
    raise SystemExit("SBP-037 install: executor constructor anchor not found")

old_read = '''    def read_state(self, app_id: str) -> LifecycleState:
        operation = self.bridge.execute("state", app_id)
        return native_state_snapshot(app_id, operation, self.engine)
'''
new_read = '''    def read_state(self, app_id: str) -> LifecycleState:
        if self.state_provider is not None:
            canonical = self.state_provider.read_state(app_id, self.engine)
            if canonical is not None:
                return canonical
        operation = self.bridge.execute("state", app_id)
        return native_state_snapshot(app_id, operation, self.engine)
'''
if old_read in s:
    s = s.replace(old_read, new_read, 1)
elif "canonical = self.state_provider.read_state" not in s:
    raise SystemExit("SBP-037 install: executor read_state anchor not found")
executor.write_text(s)

s = init.read_text()
if "CanonicalRuntimeStateProvider" not in s:
    s += '\nfrom .runtime_state import (\n    CANONICAL_RUNTIME_STATES,\n    CanonicalRuntimeStateProvider,\n    RuntimeStateObservation,\n)\n'
init.write_text(s)

s = routes.read_text()
if "CanonicalRuntimeStateProvider," not in s:
    anchor = "                AppLifecycleEngine,\n"
    if anchor not in s:
        raise SystemExit("SBP-037 install: lifecycle route import anchor not found")
    s = s.replace(anchor, anchor + "                CanonicalRuntimeStateProvider,\n", 1)

old = "        executor = LifecycleExecutor(bridge, AppLifecycleEngine())\n"
new = '''        state_provider = CanonicalRuntimeStateProvider()
        executor = LifecycleExecutor(
            bridge,
            AppLifecycleEngine(),
            state_provider=state_provider,
        )
'''
if old in s:
    s = s.replace(old, new, 1)
elif "state_provider=state_provider" not in s:
    raise SystemExit("SBP-037 install: LifecycleExecutor route anchor not found")
routes.write_text(s)
PATCHPY

python3 -m py_compile   "$ROOT/shared/app_lifecycle/"*.py   "$ROOT/seymour-blockchain-manager/data/web/lifecycle_routes.py"

printf '%s\n' "$BACKUP" > "$ROOT/backups/sbp-037-latest"

echo "Backup: $BACKUP"
echo "SBP-037 install: canonical runtime state provider PASS"
echo "SBP-037 install: lifecycle executor reconciliation wiring PASS"
echo "SBP-037 install: PASS"
echo "No live Umbrel lifecycle write action was executed."
echo "Blockchain Manager restart was NOT performed by install.sh."
