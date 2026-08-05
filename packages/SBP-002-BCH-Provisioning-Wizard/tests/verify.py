import importlib.util
import sys
from pathlib import Path

repo = Path(sys.argv[1])
status = repo / "seymour-bch-node/data/status"

for rel in ("provisioning.py", "templates/provision.html"):
    assert (status / rel).is_file(), rel

spec = importlib.util.spec_from_file_location(
    "provisioning",
    status / "provisioning.py",
)
module = importlib.util.module_from_spec(spec)
sys.modules["provisioning"] = module
spec.loader.exec_module(module)

fresh = module.build_plan({
    "experience": "recommended",
    "mode": "fresh-sync",
})
assert fresh["validation"]["valid"] is True
assert fresh["versionProfile"] == "seymour-recommended"
assert fresh["executable"] is False

bad_copy = module.build_plan({
    "experience": "advanced",
    "mode": "copy-existing",
})
assert bad_copy["validation"]["valid"] is False
assert len(bad_copy["validation"]["errors"]) == 2

remote = module.build_plan({
    "experience": "advanced",
    "mode": "remote-rpc",
    "rpcHost": "192.168.1.156",
    "rpcPort": "8332",
    "rpcUser": "rpc",
    "rpcPassword": "secret",
})
assert remote["validation"]["valid"] is True
assert remote["inputs"]["rpcPasswordProvided"] is True
assert "rpcPassword" not in remote["inputs"]

app = (status / "app.py").read_text()
assert "/api/provisioning/plan" in app
assert 'self.path == "/provision"' in app

print("SBP-002 BCH Provisioning Wizard verification: PASS")
