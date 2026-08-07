from pathlib import Path
import importlib.util, os, sys, tempfile
os.environ["NEXUS_REGISTRATION_URL"]=""
os.environ["NEXUS_REGISTRATION_TOKEN"]=""
repo=Path(__file__).resolve().parents[1]

web = repo / "seymour-blockchain-manager/data/web"

if str(web) not in sys.path:
    sys.path.insert(0, str(web))
path=repo/"seymour-blockchain-manager/data/web/nexus_scheduler.py"
spec=importlib.util.spec_from_file_location("sbp019_scheduler",path); m=importlib.util.module_from_spec(spec); sys.modules[spec.name]=m; spec.loader.exec_module(m)
assert m.INTERVAL_SECONDS >= 30
assert m.status()["configured"] is False
with tempfile.TemporaryDirectory() as d:
    m.STATE_PATH=Path(d)/"state.json"
    result=m.refresh_once()
    assert result["status"]=="not-configured"
    assert m.STATE_PATH.is_file()
print("SBP-019 scheduler state verification: PASS")
