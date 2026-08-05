from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


repo = Path(sys.argv[1]).resolve()
shared = repo / "shared"

sys.path.insert(
    0,
    str(shared),
)

from umbrel_runtime import UmbrelRuntime


with tempfile.TemporaryDirectory() as temp:
    data_directory = Path(temp)
    app_data = data_directory / "app-data"
    app_data.mkdir()

    installed = app_data / "seymour-bch-node"
    installed.mkdir()

    runtime = UmbrelRuntime(
        data_directory=data_directory,
        app_store_root=repo,
        docker_binary="false",
    )

    source_apps = runtime.list_source_apps()

    assert "seymour-bch-node" in source_apps
    assert "seymour-bitcoin-node" in source_apps

    installed_apps = runtime.list_installed_apps()

    assert installed_apps == [
        "seymour-bch-node"
    ]

    state = runtime.inspect_app(
        "seymour-bch-node"
    ).to_dict()

    assert state["installed"] is True
    assert state["source_available"] is True
    assert state["version"] == "0.2.0-alpha"
    assert state["lifecycle_status"] == (
        "installed-stopped"
    )
    assert state["containers"] == []

    missing = runtime.inspect_app(
        "seymour-bitcoin-node"
    ).to_dict()

    assert missing["installed"] is False
    assert missing["lifecycle_status"] == (
        "not-installed"
    )

wrapper = (
    repo
    / "scripts"
    / "seymour-umbrel-runtime"
)

assert wrapper.is_file()
assert wrapper.stat().st_mode & 0o111

print(
    "SBP-004 Umbrel Runtime Integration "
    "verification: PASS"
)
