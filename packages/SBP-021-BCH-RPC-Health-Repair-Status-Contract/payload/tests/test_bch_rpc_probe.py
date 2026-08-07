from pathlib import Path
import importlib.util,sys
repo=Path(__file__).resolve().parents[1]
web=repo/"seymour-blockchain-manager/data/web"
sys.path.insert(0,str(web))
spec=importlib.util.spec_from_file_location("sbp021",web/"bch_rpc_probe.py")
m=importlib.util.module_from_spec(spec); sys.modules[spec.name]=m; spec.loader.exec_module(m)
assert m._rpc_headers()["Content-Type"]=="application/json"
assert m.RPC_TIMEOUT_SECONDS>=1
print("SBP-021 BCH RPC probe verification: PASS")
