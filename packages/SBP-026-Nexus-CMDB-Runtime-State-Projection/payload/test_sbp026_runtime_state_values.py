from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

repo = Path(__file__).resolve().parents[1]
path = repo / "seymour-blockchain-manager" / "data" / "web" / "runtime_state.py"

spec = spec_from_file_location("sbp026_runtime_state", path)
module = module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

normalize = module.normalize_runtime_state

syncing = normalize({
    "installed": True,
    "running": True,
    "container": {"health": "healthy"},
    "rpc": {"probe": {
        "reachable": True,
        "healthy": True,
        "status": "healthy",
        "initialBlockDownload": True,
        "verificationProgress": 0.42,
    }},
})
assert syncing["state"] == "syncing"
assert syncing["verificationProgress"] == 0.42

healthy = normalize({
    "installed": True,
    "running": True,
    "container": {"health": "healthy"},
    "rpc": {"probe": {
        "reachable": True,
        "healthy": True,
        "status": "healthy",
        "initialBlockDownload": False,
        "verificationProgress": 1.0,
    }},
})
assert healthy["state"] == "healthy"

degraded = normalize({
    "installed": True,
    "running": True,
    "container": {"health": "healthy"},
    "rpc": {"probe": {
        "reachable": False,
        "healthy": False,
    }},
})
assert degraded["state"] == "degraded"

print("SBP-026 runtime-state value verification: PASS")
