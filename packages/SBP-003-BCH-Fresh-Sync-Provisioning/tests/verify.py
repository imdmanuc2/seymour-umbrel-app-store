from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path


repo = Path(sys.argv[1]).resolve()
status_dir = (
    repo
    / "seymour-bch-node"
    / "data"
    / "status"
)

with tempfile.TemporaryDirectory() as temp:
    os.environ[
        "BCH_PROVISIONING_STATE_DIR"
    ] = temp

    spec = importlib.util.spec_from_file_location(
        "provisioning",
        status_dir / "provisioning.py",
    )
    module = importlib.util.module_from_spec(
        spec
    )
    sys.modules["provisioning"] = module
    spec.loader.exec_module(module)

    plan = module.build_plan(
        {
            "experience": "recommended",
            "mode": "fresh-sync",
        }
    )

    assert plan["validation"]["valid"] is True
    assert plan["executable"] is True
    assert plan["runtime"]["txindex"] is True
    assert plan["runtime"]["prune"] == 0

    module.save_plan(plan)
    loaded = module.load_plan()

    assert loaded["mode"] == "fresh-sync"

    first = module.ensure_rpc_secrets()
    second = module.ensure_rpc_secrets()

    assert first == second
    assert first["rpcUser"] == "seymour_rpc"
    assert len(first["rpcPassword"]) >= 32

app_text = (
    status_dir / "app.py"
).read_text()

assert "/api/provisioning/apply" in app_text
assert "/api/provisioning/status" in app_text
assert "/api/readiness" in app_text
assert "/api/storage" in app_text

compose = (
    repo
    / "seymour-bch-node"
    / "docker-compose.yml"
).read_text()

assert "${APP_DATA_DIR}/data/state:/state" in compose
assert "BCH_PROVISIONING_STATE_DIR" in compose

entrypoint = (
    repo
    / "seymour-bch-node"
    / "data"
    / "node"
    / "entrypoint.sh"
).read_text()

assert "provisioning-plan.json" in entrypoint
assert "rpc-secrets.json" in entrypoint
assert "zmqpubrawblock" in entrypoint
assert "zmqpubrawtx" in entrypoint

print(
    "SBP-003 BCH Fresh Sync Provisioning "
    "verification: PASS"
)
