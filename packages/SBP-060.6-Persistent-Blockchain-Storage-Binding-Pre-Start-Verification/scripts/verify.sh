#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
echo "SBP-060.6 verify: persistent blockchain storage binding"
python3 -m py_compile \
  "$ROOT/shared/blockchain_install/runtime_binding.py" \
  "$ROOT/shared/blockchain_install/prestart_guard.py"
PYTHONPATH="$ROOT" python3 - <<'PY'
from pathlib import Path
from tempfile import TemporaryDirectory
from shared.blockchain_install.runtime_binding import persist_runtime_binding, verify_live_data_mount

with TemporaryDirectory() as td:
    root=Path(td)
    compose=root/"docker-compose.yml"
    compose.write_text(
        "services:\n  node:\n    volumes:\n"
        "      - ${SEYMOUR_BLOCKCHAIN_DATA_PATH:-${APP_DATA_DIR}/data/node}:/data\n"
        "  status:\n    volumes:\n"
        "      - ${SEYMOUR_BLOCKCHAIN_DATA_PATH:-${APP_DATA_DIR}/data/node}:/node-data\n"
    )
    data=root/"chain"; data.mkdir()
    persist_runtime_binding(
        provider_id="bitcoin-cash-mainnet",
        app_id="seymour-bch-node",
        compose_path=compose,
        data_path=data,
    )
    text=compose.read_text()
    assert f"{data}:/data" in text
    assert f"{data}:/node-data" in text
print("SBP-060.6 persistent binding regression test: PASS")

ok=verify_live_data_mount(
    inspect_mounts=[{"Source":"/mnt/seymour-storage/bitcoin-cash-mainnet","Destination":"/data"}],
    expected_data_path=Path("/mnt/seymour-storage/bitcoin-cash-mainnet"),
)
assert ok["healthy"]

bad=verify_live_data_mount(
    inspect_mounts=[{"Source":"/home/umbrel/umbrel/app-data/seymour-bch-node/data/node","Destination":"/data"}],
    expected_data_path=Path("/mnt/seymour-storage/bitcoin-cash-mainnet"),
)
assert not bad["healthy"]
assert bad["error"]=="storage-binding-mismatch"
print("SBP-060.6 live mount identity contract: PASS")
print("SBP-060.6 fail-closed mismatch contract: PASS")
PY
echo "SBP-060.6 final verification: PASS"
echo "No live runtime was restarted or modified."
