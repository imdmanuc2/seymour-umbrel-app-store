from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


repo = Path(sys.argv[1]).resolve()
sys.path.insert(
    0,
    str(repo / "shared"),
)

from bch_install import BchInstallWorkflow


with tempfile.TemporaryDirectory() as temp:
    data = Path(temp)
    (data / "app-stores").mkdir()
    (data / "secrets").mkdir()
    (data / "secrets" / "jwt").write_text(
        "0" * 64
    )

    store = (
        data
        / "app-stores"
        / "imdmanuc2-seymour-umbrel-app-store-test"
        / "seymour-bch-node"
    )
    store.mkdir(parents=True)

    (store / "umbrel-app.yml").write_text(
        'id: seymour-bch-node\n'
        'version: "0.2.2-alpha"\n'
    )

    workflow = BchInstallWorkflow(
        repository=repo,
        data_directory=data,
        control_script=(
            repo
            / "scripts"
            / "seymour-umbrel-app"
        ),
        runtime_script=(
            repo
            / "scripts"
            / "seymour-umbrel-runtime"
        ),
        evidence_directory=(
            data / "evidence"
        ),
        minimum_free_bytes=1,
    )

    preflight = workflow.preflight()

    assert preflight["compatible"] is True
    assert (
        preflight["checks"][
            "appStoreVersion"
        ]
        == "0.2.2-alpha"
    )

    plan = workflow.installation_plan()

    assert plan["mode"] == "plan"
    assert plan["compatible"] is True
    assert (
        plan["requiredConfirmation"]
        == "INSTALL-seymour-bch-node"
    )
    assert (
        plan["automaticUninstallOnFailure"]
        is False
    )

    evidence = workflow.install(
        execute=False
    )

    assert evidence.status == "planned"
    assert evidence.mode == "plan"
    assert evidence.install_result is None

    evidence_files = list(
        (data / "evidence").glob("*.json")
    )

    assert len(evidence_files) == 1
    json.loads(
        evidence_files[0].read_text()
    )

wrapper = (
    repo
    / "scripts"
    / "seymour-install-bch"
)

assert wrapper.is_file()
assert wrapper.stat().st_mode & 0o111

print(
    "SBP-006 BCH Installation Workflow "
    "verification: PASS"
)
