from pathlib import Path
import importlib.util
import sys
import tempfile
repo = Path(__file__).resolve().parents[1]
path = repo / "seymour-blockchain-manager/data/web/installer.py"
spec = importlib.util.spec_from_file_location("sbp011_installer", path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
credentials = module.generate_credentials()
assert credentials["rpcUser"] == "seymour_rpc"
assert len(credentials["rpcPassword"]) >= 32
request = module.InstallRequest.from_dict({"providerId":"bitcoin-cash-mainnet","appId":"seymour-bch-node","nodeName":"Test","rpcUser":"seymour_rpc","rpcPassword":"a"*32,"rpcPort":8332,"p2pPort":8333,"confirmation":"INSTALL-seymour-bch-node"})
module.validate_request(request)
with tempfile.TemporaryDirectory() as directory:
    operation = module.InstallOperation("test", module.InstallStatus.PLANNED, module.utc_now(), module.utc_now(), {"rpc_password":"secret"}, {"compatible":True})
    installer = module.Installer(operations_path=Path(directory)/"operations", evidence_path=Path(directory)/"evidence.jsonl")
    installer._save(operation)
    assert installer.load("test")["request"]["rpc_password"] == "[REDACTED]"
print("SBP-011 installation wizard verification: PASS")
