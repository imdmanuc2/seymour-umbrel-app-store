#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"

echo "SBP-060.7 verify: runtime start storage guard integration"

python3 -m py_compile \
  "$ROOT/shared/blockchain_install/start_guard.py" \
  "$ROOT/shared/umbrel_control/bridge.py"

PYTHONPATH="$ROOT" python3 - <<'PY'
from pathlib import Path
from tempfile import TemporaryDirectory

from shared.blockchain_install.start_guard import (
    resolve_storage_expectation,
    verify_expected_path,
)

with TemporaryDirectory() as td:
    root = Path(td)

    app = (
        root
        / "app-data"
        / "seymour-bch-node"
    )
    app.mkdir(parents=True)

    (
        app / "docker-compose.yml"
    ).write_text(
        "services:\n"
        "  node:\n"
        "    volumes:\n"
        "      - "
        "${SEYMOUR_BLOCKCHAIN_DATA_PATH"
        ":-${APP_DATA_DIR}/data/node}"
        ":/data\n"
    )

    try:
        resolve_storage_expectation(
            data_directory=root,
            app_id="seymour-bch-node",
        )
    except RuntimeError:
        pass
    else:
        raise AssertionError(
            "unpersisted binding not blocked"
        )

print(
    "SBP-060.7 unresolved binding "
    "fail-closed contract: PASS"
)

with TemporaryDirectory() as td:
    root = Path(td)
    data = root / "chain"
    data.mkdir()

    app = (
        root
        / "app-data"
        / "seymour-bch-node"
    )
    app.mkdir(parents=True)

    (
        app / "docker-compose.yml"
    ).write_text(
        "services:\n"
        "  node:\n"
        "    volumes:\n"
        f"      - {data}:/data\n"
        "  status:\n"
        "    volumes:\n"
        f"      - {data}:/node-data\n"
    )

    expectation = (
        resolve_storage_expectation(
            data_directory=root,
            app_id="seymour-bch-node",
        )
    )

    assert expectation is not None
    assert (
        expectation.status_data_path
        == expectation.data_path
    )

    result = verify_expected_path(
        expectation
    )

    assert result["healthy"] is True

print(
    "SBP-060.7 persisted dual-binding "
    "contract: PASS"
)
PY

grep -q \
  'resolve_storage_expectation' \
  "$ROOT/shared/umbrel_control/bridge.py"

grep -q \
  'verify_expected_path' \
  "$ROOT/shared/umbrel_control/bridge.py"

grep -q \
  'delegated-to-privileged-runtime-observer' \
  "$ROOT/shared/umbrel_control/bridge.py"

if grep -q \
  'wait_for_live_binding' \
  "$ROOT/shared/umbrel_control/bridge.py"
then
  echo "SBP-060.7 obsolete post-start Docker guard still present"
  exit 1
fi

echo "SBP-060.7 native pre-start bridge contract: PASS"
echo "SBP-060.7 privilege-boundary contract: PASS"
echo "SBP-060.7 final verification: PASS"
echo "No live runtime was restarted or modified."
