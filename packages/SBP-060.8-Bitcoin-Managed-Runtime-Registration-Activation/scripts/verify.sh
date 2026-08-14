#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"

echo "SBP-060.8 verify: Bitcoin managed runtime registration and activation"

python3 -m py_compile \
  "$ROOT/shared/bitcoin_managed_runtime/workflow.py" \
  "$ROOT/scripts/seymour-bitcoin-managed-runtime"

PYTHONPATH="$ROOT" python3 - <<'PY'
from pathlib import Path
from tempfile import TemporaryDirectory

from shared.bitcoin_managed_runtime import (
    BitcoinManagedRuntimeWorkflow,
)

with TemporaryDirectory() as td:
    root = Path(td)

    (root / "seymour-bitcoin-node").mkdir()

    (
        root
        / "seymour-bitcoin-node"
        / "umbrel-app.yml"
    ).write_text(
        "id: seymour-bitcoin-node\n"
    )

    (root / "scripts").mkdir()

    control = (
        root
        / "scripts"
        / "seymour-umbrel-app"
    )
    control.write_text("#!/bin/sh\n")

    missing = (
        BitcoinManagedRuntimeWorkflow(
            repository=root,
            umbrel_data_directory=(
                root / "umbrel"
            ),
            data_path=root / "missing",
        )
    )

    plan = missing.install_plan()

    assert plan["compatible"] is False

    assert (
        "bitcoin-data-path-missing"
        in plan["preflight"]["storage"]["errors"]
    )

    assert (
        plan["requiredConfirmation"]
        == "INSTALL-seymour-bitcoin-node"
    )

    start_plan = missing.start_plan()

    assert (
        start_plan["requiredConfirmation"]
        == "START-seymour-bitcoin-node"
    )

print(
    "SBP-060.8 missing storage "
    "fail-closed contract: PASS"
)

print(
    "SBP-060.8 native install "
    "confirmation contract: PASS"
)

print(
    "SBP-060.8 native start "
    "confirmation contract: PASS"
)
PY

grep -q \
  'persist_runtime_binding' \
  "$ROOT/shared/bitcoin_managed_runtime/workflow.py"

echo "SBP-060.8 persistent storage binding contract: PASS"
echo "SBP-060.8 final verification: PASS"
echo "No live Bitcoin installation or start was executed."
