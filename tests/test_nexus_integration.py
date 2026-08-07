from pathlib import Path
import importlib.util
import json
import sys
import tempfile

repo = Path(__file__).resolve().parents[1]

import os

os.environ["PROVIDER_CATALOG_PATH"] = str(
    repo / "shared/provider_catalog/providers.v1.json"
)

path = repo / "seymour-blockchain-manager/data/web/nexus_integration.py"

spec = importlib.util.spec_from_file_location("sbp015_nexus", path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

dashboard = {
    "providers": {
        "bitcoin-cash-mainnet": {
            "lifecycleStatus": "running",
            "rpc": {"reachable": True},
        }
    }
}
sync = {
    "providerId": "bitcoin-cash-mainnet",
    "blocksRemaining": 0,
}

document = module.discovery_document(dashboard, sync)
assert document["managementPlane"] == "nexus"
assert len(document["assets"]) == 2
assert len(document["providers"]) == 9
assert "lifecycle.restart" in document["capabilities"]

payload = module.registration_payload(dashboard, sync)
assert payload["registrationId"].startswith("registration-")

with tempfile.TemporaryDirectory() as directory:
    module.EVIDENCE_PATH = Path(directory) / "registration.jsonl"
    module.append_registration_evidence(payload)
    saved = json.loads(module.EVIDENCE_PATH.read_text().splitlines()[0])
    assert saved["registrationId"] == payload["registrationId"]

print("SBP-015 Nexus integration verification: PASS")
