#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PKG="$ROOT/packages/SBP-075.3-Canonical-Runtime-Binding-Materialization"

ROOT_MODULE="$ROOT/shared/blockchain_install/runtime_binding_materializer.py"
MANAGER_MODULE="$ROOT/seymour-blockchain-manager/data/shared/blockchain_install/runtime_binding_materializer.py"

PAYLOAD="$PKG/payload/shared/blockchain_install/runtime_binding_materializer.py"

echo "===== SBP-075.3 VERIFY ====="

test -f "$ROOT_MODULE"
test -f "$MANAGER_MODULE"

cmp -s \
  "$PAYLOAD" \
  "$ROOT_MODULE"

echo "PASS: root materializer matches package"

cmp -s \
  "$PAYLOAD" \
  "$MANAGER_MODULE"

echo "PASS: Manager materializer matches package"

PYTHONDONTWRITEBYTECODE=1 \
ROOT="$ROOT" \
python3 - <<'PY'
import os
import sys
import tempfile
from pathlib import Path

root = Path(os.environ["ROOT"])

sys.path.insert(
    0,
    str(root),
)

from shared.blockchain_install.runtime_binding import (
    RuntimeBinding,
    RuntimeBindingMode,
)

from shared.blockchain_install.runtime_binding_materializer import (
    materialize_runtime_binding,
)


def single_path_test() -> None:
    with tempfile.TemporaryDirectory() as temp:
        compose = Path(temp) / "docker-compose.yml"

        compose.write_text(
            "services:\n"
            "  node:\n"
            "    volumes:\n"
            "      - ${SEYMOUR_BLOCKCHAIN_DATA_PATH:-"
            "${APP_DATA_DIR}/data/node}:/data\n"
            "  status:\n"
            "    volumes:\n"
            "      - ${SEYMOUR_BLOCKCHAIN_DATA_PATH:-"
            "${APP_DATA_DIR}/data/node}:/node-data:ro\n"
        )

        binding = RuntimeBinding(
            provider_id="monero-mainnet",
            app_id="seymour-monero-node",
            mode=RuntimeBindingMode.SINGLE_PATH,
            data_path=Path(
                "/mnt/seymour-storage/monero-mainnet"
            ),
        )

        result = materialize_runtime_binding(
            compose_path=compose,
            binding=binding,
        )

        text = compose.read_text()

        assert result["mode"] == "single-path"
        assert result["anchorsResolved"] == 2
        assert result["anchorsExpected"] == 2

        assert (
            "/mnt/seymour-storage/"
            "monero-mainnet:/data"
            in text
        )

        assert (
            "/mnt/seymour-storage/"
            "monero-mainnet:/node-data:ro"
            in text
        )

        assert (
            "SEYMOUR_BLOCKCHAIN_DATA_PATH"
            not in text
        )

        second = materialize_runtime_binding(
            compose_path=compose,
            binding=binding,
        )

        assert second["anchorsResolved"] == 2
        assert second["changed"] is False

    print("PASS: single-path materialization")
    print("PASS: single-path materialization idempotent")


def hybrid_test() -> None:
    with tempfile.TemporaryDirectory() as temp:
        compose = Path(temp) / "docker-compose.yml"

        compose.write_text(
            "services:\n"
            "  node:\n"
            "    volumes:\n"
            "      - ${SEYMOUR_BLOCKCHAIN_LOCAL_DATA_PATH:-"
            "${APP_DATA_DIR}/data/node}:/data\n"
            "      - ${SEYMOUR_BLOCKCHAIN_BLOCKS_PATH:-"
            "${APP_DATA_DIR}/data/node/blocks}:"
            "/data/blocks\n"
            "  status:\n"
            "    volumes:\n"
            "      - ${SEYMOUR_BLOCKCHAIN_LOCAL_DATA_PATH:-"
            "${APP_DATA_DIR}/data/node}:/node-data\n"
            "      - ${SEYMOUR_BLOCKCHAIN_BLOCKS_PATH:-"
            "${APP_DATA_DIR}/data/node/blocks}:"
            "/node-data/blocks\n"
        )

        binding = RuntimeBinding(
            provider_id="bitcoin-cash-mainnet",
            app_id="seymour-bch-node",
            mode=RuntimeBindingMode.HYBRID_BLOCKS,
            local_data_path=Path(
                "/home/umbrel/umbrel/app-data/"
                "seymour-bch-node/data/node"
            ),
            blocks_path=Path(
                "/mnt/seymour-storage/"
                "bitcoin-cash-mainnet/blocks"
            ),
        )

        result = materialize_runtime_binding(
            compose_path=compose,
            binding=binding,
        )

        text = compose.read_text()

        assert result["mode"] == "hybrid-blocks"
        assert result["anchorsResolved"] == 4
        assert result["anchorsExpected"] == 4

        assert (
            "/home/umbrel/umbrel/app-data/"
            "seymour-bch-node/data/node:/data"
            in text
        )

        assert (
            "/mnt/seymour-storage/"
            "bitcoin-cash-mainnet/blocks:"
            "/data/blocks"
            in text
        )

        assert (
            "/home/umbrel/umbrel/app-data/"
            "seymour-bch-node/data/node:"
            "/node-data"
            in text
        )

        assert (
            "/mnt/seymour-storage/"
            "bitcoin-cash-mainnet/blocks:"
            "/node-data/blocks"
            in text
        )

        second = materialize_runtime_binding(
            compose_path=compose,
            binding=binding,
        )

        assert second["anchorsResolved"] == 4
        assert second["changed"] is False

    print("PASS: hybrid-blocks materialization")
    print("PASS: hybrid-blocks materialization idempotent")


single_path_test()
hybrid_test()
PY

echo
echo "===== BYTECODE SAFETY ====="

if find "$PKG" \
  \( \
    -type d -name '__pycache__' \
    -o -type f -name '*.pyc' \
    -o -type f -name '*.pyo' \
  \) \
  -print -quit \
  | grep -q .
then
    echo "ERROR: package verification created bytecode"
    exit 1
fi

echo "PASS: verification created no package bytecode"

echo
echo "===== LIVE RUNTIME NON-INTERFERENCE ====="

sudo docker inspect \
  seymour-monero-node_node_1 \
  --format 'status={{.State.Status}} health={{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}} restarts={{.RestartCount}}'

echo
echo "SBP-075.3 VERIFY PASS"
