#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$ROOT/backups/sbp-038-$STAMP"

"$PKG/scripts/doctor.sh" "$ROOT"

mkdir -p "$BACKUP/web" "$BACKUP/app_lifecycle"
cp -a "$ROOT/seymour-blockchain-manager/data/web/runtime_state.py" "$BACKUP/web/runtime_state.py"
cp -a "$ROOT/seymour-blockchain-manager/data/web/lifecycle_routes.py" "$BACKUP/web/lifecycle_routes.py"
cp -a "$ROOT/shared/app_lifecycle/runtime_state.py" "$BACKUP/app_lifecycle/runtime_state.py"

mkdir -p "$ROOT/shared/runtime_state"
cp -a "$PKG/payload/shared/runtime_state/service.py" "$ROOT/shared/runtime_state/service.py"
cp -a "$PKG/payload/shared/runtime_state/__init__.py" "$ROOT/shared/runtime_state/__init__.py"

cat > "$ROOT/seymour-blockchain-manager/data/web/runtime_state.py" <<'WRAPPER'
from __future__ import annotations

import os
import sys
from pathlib import Path

platform_root = Path(os.environ.get("SEYMOUR_PLATFORM_ROOT", "/seymour-platform"))
root_text = str(platform_root)
if root_text not in sys.path:
    sys.path.insert(0, root_text)

from shared.runtime_state import (
    CANONICAL_RUNTIME_STATES,
    RuntimeStateService,
    normalize_runtime_state,
)

VALID_RUNTIME_STATES = set(CANONICAL_RUNTIME_STATES)

__all__ = [
    "CANONICAL_RUNTIME_STATES",
    "VALID_RUNTIME_STATES",
    "RuntimeStateService",
    "normalize_runtime_state",
]
WRAPPER

python3 - "$ROOT" <<'PATCHPY'
from pathlib import Path
import sys

root = Path(sys.argv[1])
provider = root / "shared/app_lifecycle/runtime_state.py"
routes = root / "seymour-blockchain-manager/data/web/lifecycle_routes.py"

s = provider.read_text()

if "app_probes:" not in s:
    s = s.replace(
        "        app_urls: Mapping[str, str] | None = None,\n        timeout_seconds: float = 10.0,\n",
        "        app_urls: Mapping[str, str] | None = None,\n        app_probes: Mapping[str, Any] | None = None,\n        timeout_seconds: float = 3.0,\n",
        1,
    )
    s = s.replace(
        "        self.timeout_seconds = float(timeout_seconds)\n",
        "        self.app_probes = dict(app_probes or {})\n        self.timeout_seconds = float(timeout_seconds)\n",
        1,
    )

if "probe = self.app_probes.get(app_id)" not in s:
    anchor = (
        "    def observe(self, app_id: str) -> RuntimeStateObservation | None:\n"
        "        url = self.app_urls.get(app_id)\n"
        "        if not url:\n"
        "            return None\n"
    )
    replacement = (
        "    def observe(self, app_id: str) -> RuntimeStateObservation | None:\n"
        "        probe = self.app_probes.get(app_id)\n"
        "        if probe is not None:\n"
        "            try:\n"
        "                raw = probe()\n"
        "                state_payload = raw.get('operationalState') if isinstance(raw, dict) else None\n"
        "                state_payload = state_payload if isinstance(state_payload, dict) else {}\n"
        "                runtime_state = str(state_payload.get('state') or 'unknown').strip().lower()\n"
        "                if runtime_state not in CANONICAL_RUNTIME_STATES:\n"
        "                    runtime_state = 'unknown'\n"
        "                return RuntimeStateObservation(\n"
        "                    app_id=app_id,\n"
        "                    runtime_state=runtime_state,\n"
        "                    payload={\n"
        "                        'runtimeState': runtime_state,\n"
        "                        'runtimeStateReason': state_payload.get('reason'),\n"
        "                        'runtimeRpcReachable': state_payload.get('rpcReachable'),\n"
        "                        'runtimeRpcHealthy': state_payload.get('rpcHealthy'),\n"
        "                        'runtimeInitialBlockDownload': state_payload.get('initialBlockDownload'),\n"
        "                        'runtimeVerificationProgress': state_payload.get('verificationProgress'),\n"
        "                        'operationalState': state_payload,\n"
        "                    },\n"
        "                    source='direct-runtime-probe',\n"
        "                )\n"
        "            except Exception as exc:\n"
        "                return RuntimeStateObservation(\n"
        "                    app_id=app_id,\n"
        "                    runtime_state='unknown',\n"
        "                    payload={'runtimeState': 'unknown', 'error': str(exc)},\n"
        "                    source='direct-runtime-probe',\n"
        "                )\n"
        "\n"
        "        url = self.app_urls.get(app_id)\n"
        "        if not url:\n"
        "            return None\n"
    )
    if anchor not in s:
        raise SystemExit("SBP-038 install: provider observe anchor missing")
    s = s.replace(anchor, replacement, 1)

provider.write_text(s)

s = routes.read_text()
if "from bch_runtime_probe import probe as probe_bch_runtime" not in s:
    s = s.replace(
        "from typing import Any, Mapping\n",
        "from typing import Any, Mapping\n\nfrom bch_runtime_probe import probe as probe_bch_runtime\n",
        1,
    )

if "app_probes={" not in s:
    old = "        state_provider = CanonicalRuntimeStateProvider()\n"
    new = (
        "        bch_app_id = os.environ.get('BCH_APP_ID', 'seymour-bch-node')\n"
        "        state_provider = CanonicalRuntimeStateProvider(\n"
        "            app_urls={},\n"
        "            app_probes={bch_app_id: probe_bch_runtime},\n"
        "            timeout_seconds=3.0,\n"
        "        )\n"
    )
    if old not in s:
        raise SystemExit("SBP-038 install: lifecycle provider construction anchor missing")
    s = s.replace(old, new, 1)

routes.write_text(s)
PATCHPY

python3 -m py_compile \
  "$ROOT/shared/runtime_state/"*.py \
  "$ROOT/shared/app_lifecycle/runtime_state.py" \
  "$ROOT/seymour-blockchain-manager/data/web/runtime_state.py" \
  "$ROOT/seymour-blockchain-manager/data/web/bch_runtime_probe.py" \
  "$ROOT/seymour-blockchain-manager/data/web/lifecycle_routes.py"

printf '%s\n' "$BACKUP" > "$ROOT/backups/sbp-038-latest"

echo "Backup: $BACKUP"
echo "SBP-038 shared canonical runtime-state service: PASS"
echo "SBP-038 direct lifecycle probe wiring: PASS"
echo "SBP-038 install: PASS"
echo "No live Umbrel lifecycle write action was executed."
echo "Blockchain Manager restart was NOT performed by install.sh."
