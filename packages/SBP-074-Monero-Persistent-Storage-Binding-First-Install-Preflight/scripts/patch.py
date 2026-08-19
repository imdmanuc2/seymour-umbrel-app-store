#!/usr/bin/env python3
from pathlib import Path
import sys

root=Path(sys.argv[1])
hook=root/"seymour-monero-node/hooks/pre-install"
text=hook.read_text()

if "runtime-bindings" in text and "SEYMOUR_BLOCKCHAIN_DATA_PATH" in text:
    print("SBP-074 Monero hook storage binding already present")
    raise SystemExit(0)

text=text.replace(
    'COMPOSE="$APP_DATA_DIR/docker-compose.yml"\n\napp_id="$(basename "$APP_DATA_DIR")"\n',
    'COMPOSE="$APP_DATA_DIR/docker-compose.yml"\nUMBREL_ROOT="${UMBREL_ROOT:-$(cd "$APP_DATA_DIR/../.." && pwd)}"\n\napp_id="$(basename "$APP_DATA_DIR")"\nBINDING_FILE="$UMBREL_ROOT/app-data/seymour-blockchain-manager/data/evidence/runtime-bindings/$app_id.env"\n',
    1,
)

text=text.replace(
    'rpc_host="${app_id}-rpc"\nstatus_host="${app_id}-status"\n\npython3 - "$COMPOSE" "$rpc_host" "$status_host" <<\'PY\'\n',
    '''rpc_host="${app_id}-rpc"
status_host="${app_id}-status"

data_path=""

if [[ -f "$BINDING_FILE" ]]; then
  while IFS='=' read -r key value; do
    case "$key" in
      SEYMOUR_BLOCKCHAIN_DATA_PATH)
        data_path="$value"
        ;;
    esac
  done < "$BINDING_FILE"
fi

if [[ -z "$data_path" || "$data_path" != /* || "$data_path" == *$'\\n'* || "$data_path" == *$'\\r'* ]]; then
  echo "Seymour Monero storage binding is missing or invalid: $BINDING_FILE" >&2
  exit 1
fi

python3 - "$COMPOSE" "$rpc_host" "$status_host" "$data_path" <<'PY'
''',
    1,
)

text=text.replace(
    'status_host = sys.argv[3]\n\ntext = compose.read_text()\n',
    'status_host = sys.argv[3]\ndata_path = sys.argv[4]\n\ntext = compose.read_text()\n',
    1,
)

text=text.replace(
    '    "- ${SEYMOUR_BLOCKCHAIN_STATUS_HOST}": f"- {status_host}",\n}',
    '    "- ${SEYMOUR_BLOCKCHAIN_STATUS_HOST}": f"- {status_host}",\n'
    '    "${SEYMOUR_BLOCKCHAIN_DATA_PATH:-${APP_DATA_DIR}/data/node}:/data": f"{data_path}:/data",\n'
    '    "${SEYMOUR_BLOCKCHAIN_DATA_PATH:-${APP_DATA_DIR}/data/node}:/node-data": f"{data_path}:/node-data",\n'
    '}',
    1,
)

required=[
    "runtime-bindings",
    "SEYMOUR_BLOCKCHAIN_DATA_PATH",
    'f"{data_path}:/data"',
    'f"{data_path}:/node-data"',
]
for marker in required:
    if marker not in text:
        raise SystemExit(f"ERROR: patch marker missing: {marker}")

hook.write_text(text)
print("SBP-074 Monero hook storage-binding patch: PASS")
