from pathlib import Path
import importlib.util
import sys
import tempfile

repo = Path(__file__).resolve().parents[1]
path = repo / "seymour-blockchain-manager/data/web/sync_manager.py"
spec = importlib.util.spec_from_file_location("sbp012_sync", path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

dashboard = {
    "host": {"storage": {"freeBytes": 1000 * 1000**3}},
    "providers": {"bitcoin-cash-mainnet": {
        "sync": {"height": 900, "headers": 1000, "progressPercent": 90.0},
        "peers": 8,
        "rpc": {"reachable": True},
    }},
}
snapshot = module.snapshot_from_dashboard(dashboard)
assert module.blocks_remaining(snapshot) == 100
assert module.peer_quality(8)["state"] == "good"
assert module.eta_seconds(100, 2.0) == 50
with tempfile.TemporaryDirectory() as directory:
    module.HISTORY_PATH = Path(directory) / "history.jsonl"
    result = module.analyze(dashboard)
    assert result["blocksRemaining"] == 100
    assert result["recommendations"][0]["code"] == "sync-healthy"
    assert module.HISTORY_PATH.is_file()
print("SBP-012 sync manager verification: PASS")
