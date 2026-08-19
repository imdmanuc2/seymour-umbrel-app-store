#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PKG="$ROOT/packages/SBP-073-Monero-Guarded-Installation-Adapter"

"$PKG/scripts/doctor.sh"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$ROOT/backups/sbp-073-$STAMP"

mkdir -p "$BACKUP"

cp \
  "$ROOT/seymour-blockchain-manager/data/web/installer.py" \
  "$BACKUP/installer.py"

cp \
  "$ROOT/shared/provider_catalog/providers.v1.json" \
  "$BACKUP/providers.v1.json"

python3 "$PKG/scripts/patch.py" "$ROOT"

cat > "$ROOT/scripts/seymour-install-monero" <<'SCRIPT'
#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONTROL="$ROOT/scripts/seymour-umbrel-app"

APP_ID="${XMR_APP_ID:-seymour-monero-node}"
EXPECTED="INSTALL-${APP_ID}"

EXECUTE=false
CONFIRM=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --execute)
      EXECUTE=true
      shift
      ;;
    --confirm)
      CONFIRM="${2:-}"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if [[ "$EXECUTE" != "true" ]]; then
  cat <<JSON
{
  "appId": "$APP_ID",
  "executed": false,
  "requiredConfirmation": "$EXPECTED"
}
JSON
  exit 0
fi

if [[ "$CONFIRM" != "$EXPECTED" ]]; then
  echo "Confirmation mismatch. Expected: $EXPECTED" >&2
  exit 2
fi

exec "$CONTROL" \
  install "$APP_ID" \
  --execute \
  --confirm "$EXPECTED"
SCRIPT

chmod +x "$ROOT/scripts/seymour-install-monero"

python3 -m py_compile \
  "$ROOT/seymour-blockchain-manager/data/web/installer.py"

echo "SBP-073 Monero installation adapter: PASS"
echo "SBP-073 provider selection promotion: PASS"
echo "Backup: $BACKUP"
echo "Monero was not installed."
echo "No blockchain runtime was modified."
echo "SBP-073 install: PASS"
