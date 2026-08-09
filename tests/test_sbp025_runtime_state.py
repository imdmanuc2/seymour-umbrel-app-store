from importlib.util import (
    module_from_spec,
    spec_from_file_location,
)
from pathlib import Path
import sys

repo = Path(__file__).resolve().parents[1]
path = (
    repo
    / "seymour-blockchain-manager"
    / "data"
    / "web"
    / "runtime_state.py"
)

spec = spec_from_file_location(
    "sbp025_runtime_state",
    path,
)
module = module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

normalize = module.normalize_runtime_state

cases = [
    (
        {
            "installed": False,
            "running": False,
            "container": {},
            "rpc": {"probe": {}},
        },
        "not-installed",
    ),
    (
        {
            "installed": True,
            "running": False,
            "container": {},
            "rpc": {"probe": {}},
        },
        "stopped",
    ),
    (
        {
            "installed": True,
            "running": True,
            "container": {"health": "starting"},
            "rpc": {"probe": {}},
        },
        "starting",
    ),
    (
        {
            "installed": True,
            "running": True,
            "container": {"health": "healthy"},
            "rpc": {
                "probe": {
                    "reachable": True,
                    "healthy": True,
                    "status": "healthy",
                    "initialBlockDownload": True,
                }
            },
        },
        "syncing",
    ),
    (
        {
            "installed": True,
            "running": True,
            "container": {"health": "healthy"},
            "rpc": {
                "probe": {
                    "reachable": True,
                    "healthy": True,
                    "status": "rpc-slow",
                }
            },
        },
        "syncing",
    ),
    (
        {
            "installed": True,
            "running": True,
            "container": {"health": "healthy"},
            "rpc": {
                "probe": {
                    "reachable": True,
                    "healthy": True,
                    "status": "healthy",
                    "initialBlockDownload": False,
                }
            },
        },
        "healthy",
    ),
    (
        {
            "installed": True,
            "running": True,
            "container": {"health": "healthy"},
            "rpc": {
                "probe": {
                    "reachable": False,
                    "healthy": False,
                }
            },
        },
        "degraded",
    ),
]

for payload, expected in cases:
    actual = normalize(payload)["state"]
    assert actual == expected, (
        expected,
        actual,
        payload,
    )

print(
    "SBP-025 normalized runtime state "
    "verification: PASS"
)
