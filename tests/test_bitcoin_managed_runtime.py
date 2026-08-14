from pathlib import Path
from tempfile import TemporaryDirectory

from shared.bitcoin_managed_runtime import (
    BitcoinManagedRuntimeWorkflow,
)


def test_plan_detects_missing_storage():
    with TemporaryDirectory() as td:
        root = Path(td)
        (root / "seymour-bitcoin-node").mkdir()
        (
            root
            / "seymour-bitcoin-node"
            / "umbrel-app.yml"
        ).write_text("id: seymour-bitcoin-node\n")
        (root / "scripts").mkdir()
        (
            root
            / "scripts"
            / "seymour-umbrel-app"
        ).write_text("#!/bin/sh\n")

        workflow = BitcoinManagedRuntimeWorkflow(
            repository=root,
            umbrel_data_directory=(
                root / "umbrel"
            ),
            data_path=root / "missing",
        )

        plan = workflow.install_plan()

        assert plan["compatible"] is False
        assert (
            "bitcoin-data-path-missing"
            in plan["preflight"][
                "storage"
            ]["errors"]
        )
