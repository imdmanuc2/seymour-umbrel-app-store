#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$ROOT/backups/sbp-036-$STAMP"
APP="$ROOT/seymour-blockchain-manager/data/web/app.py"
ROUTES="$ROOT/seymour-blockchain-manager/data/web/lifecycle_routes.py"
COMPOSE="$ROOT/seymour-blockchain-manager/docker-compose.yml"
TEST="$ROOT/tests/test_sbp036_http.py"

"$PKG/scripts/doctor.sh" "$ROOT"
mkdir -p "$BACKUP/seymour-blockchain-manager/data/web" "$BACKUP/tests"
cp -a "$APP" "$BACKUP/seymour-blockchain-manager/data/web/app.py"
cp -a "$COMPOSE" "$BACKUP/seymour-blockchain-manager/docker-compose.yml"
[[ -e "$ROUTES" ]] && cp -a "$ROUTES" "$BACKUP/seymour-blockchain-manager/data/web/lifecycle_routes.py"
[[ -e "$TEST" ]] && cp -a "$TEST" "$BACKUP/tests/test_sbp036_http.py"

cp "$PKG/payload/seymour-blockchain-manager/data/web/lifecycle_routes.py" "$ROUTES"
cp "$PKG/payload/tests/test_sbp036_http.py" "$TEST"

python3 - "$APP" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
s = p.read_text()

if "from lifecycle_routes import LIFECYCLE_HTTP" not in s:
    old = "from urllib.parse import unquote\n"
    new = "from urllib.parse import parse_qs, unquote, urlparse\n"
    if old not in s:
        raise SystemExit("SBP-036 install: urllib.parse import anchor missing")
    s = s.replace(old, new, 1)
    anchor = "from lifecycle import GuardedLifecycleService, LifecycleAction\n"
    if anchor not in s:
        raise SystemExit("SBP-036 install: lifecycle import anchor missing")
    s = s.replace(anchor, anchor + "from lifecycle_routes import LIFECYCLE_HTTP\n", 1)

if 'if self.path.startswith("/api/lifecycle/history"):' not in s:
    anchor = '    def do_GET(self) -> None:\n'
    block = '''    def do_GET(self) -> None:\n        if self.path.startswith("/api/lifecycle/history"):\n            query = {\n                key: values[-1]\n                for key, values in parse_qs(urlparse(self.path).query).items()\n                if values\n            }\n            payload, status = LIFECYCLE_HTTP.history(query)\n            self.send_json(payload, status=status)\n            return\n'''
    if anchor not in s:
        raise SystemExit("SBP-036 install: do_GET anchor missing")
    s = s.replace(anchor, block, 1)

if 'if self.path == "/api/lifecycle/operation":' not in s:
    anchor = '    def do_POST(self) -> None:\n'
    block = '''    def do_POST(self) -> None:\n        if self.path == "/api/lifecycle/operation":\n            try:\n                body = self.read_json_body()\n            except (ValueError, json.JSONDecodeError) as exc:\n                self.send_json({"error": "invalid-json", "message": str(exc)}, status=HTTPStatus.BAD_REQUEST)\n                return\n            payload, status = LIFECYCLE_HTTP.operation(body)\n            self.send_json(payload, status=status)\n            return\n'''
    if anchor not in s:
        raise SystemExit("SBP-036 install: do_POST anchor missing")
    s = s.replace(anchor, block, 1)

old = '''        prefix = "/api/lifecycle/"\n        if not self.path.startswith(prefix):\n            self.send_error(HTTPStatus.NOT_FOUND)\n            return\n        action = LifecycleAction(self.path[len(prefix):])\n        length = int(self.headers.get("Content-Length", "0"))\n        body = json.loads(self.rfile.read(length).decode()) if length else {}\n        result = LIFECYCLE.execute(\n            provider_id=str(body.get("providerId", "")),\n            app_id=str(body.get("appId", "")),\n            action=action,\n            confirmation=body.get("confirmation"),\n        )\n        self.send_json(result.to_dict(), status=HTTPStatus.OK if result.status.value == "succeeded" else HTTPStatus.BAD_REQUEST)\n'''
new = '''        prefix = "/api/lifecycle/"\n        if not self.path.startswith(prefix):\n            self.send_error(HTTPStatus.NOT_FOUND)\n            return\n        action = unquote(self.path[len(prefix):]).strip().lower()\n        try:\n            body = self.read_json_body()\n        except (ValueError, json.JSONDecodeError) as exc:\n            self.send_json({"error": "invalid-json", "message": str(exc)}, status=HTTPStatus.BAD_REQUEST)\n            return\n        payload, status = LIFECYCLE_HTTP.legacy_operation(action, body)\n        self.send_json(payload, status=status)\n'''
if old in s:
    s = s.replace(old, new, 1)
elif "LIFECYCLE_HTTP.legacy_operation(action, body)" not in s:
    raise SystemExit("SBP-036 install: legacy lifecycle route anchor missing")

p.write_text(s)
PY

python3 - "$COMPOSE" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
s = p.read_text()
if "SEYMOUR_PLATFORM_ROOT: /seymour-platform" not in s:
    anchor = "      SEYMOUR_UMBREL_CONTROL_SCRIPT: /control/seymour-umbrel-app\n"
    if anchor not in s:
        raise SystemExit("SBP-036 install: docker-compose environment anchor missing")
    extra = (
        anchor
        + "      SEYMOUR_PLATFORM_ROOT: /seymour-platform\n"
        + "      SEYMOUR_LIFECYCLE_AUDIT_PATH: /evidence/lifecycle-audit.jsonl\n"
        + "      SEYMOUR_LIFECYCLE_NATIVE_EVIDENCE_PATH: /evidence/native-app-control\n"
    )
    s = s.replace(anchor, extra, 1)
if "/home/umbrel/seymour-umbrel-app-store-git/shared:/seymour-platform/shared:ro" not in s:
    anchor = "      - /home/umbrel/seymour-umbrel-app-store-git/scripts:/control:ro\n"
    if anchor not in s:
        raise SystemExit("SBP-036 install: docker-compose volume anchor missing")
    s = s.replace(
        anchor,
        anchor + "      - /home/umbrel/seymour-umbrel-app-store-git/shared:/seymour-platform/shared:ro\n",
        1,
    )
p.write_text(s)
PY

python3 -m py_compile "$APP" "$ROUTES" "$TEST"
mkdir -p "$ROOT/backups"
printf '%s\n' "$BACKUP" > "$ROOT/backups/sbp-036-latest"
echo "Backup: $BACKUP"
echo "SBP-036 install: PASS"
echo "Blockchain Manager restart was NOT performed by install.sh."
echo "No live Umbrel lifecycle write action was executed."
