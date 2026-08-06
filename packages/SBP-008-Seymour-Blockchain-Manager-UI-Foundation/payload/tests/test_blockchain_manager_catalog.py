import json
from pathlib import Path


repo = Path(__file__).resolve().parents[1]
catalog_path = (
    repo
    / "seymour-blockchain-manager"
    / "data"
    / "catalog"
    / "providers.v1.json"
)

catalog = json.loads(catalog_path.read_text())

assert catalog["catalogVersion"] == "1.0.0"
assert catalog["frozen"] is True
assert len(catalog["providers"]) == 9

live = [
    provider
    for provider in catalog["providers"]
    if provider["availability"] == "live"
]

assert len(live) == 1
assert live[0]["providerId"] == "bitcoin-cash-mainnet"
assert live[0]["selectable"] is True
assert live[0]["productionImage"]

planned = [
    provider
    for provider in catalog["providers"]
    if provider["availability"] == "planned"
]

assert len(planned) == 8
assert all(provider["selectable"] is False for provider in planned)
assert all(provider["productionImage"] is None for provider in planned)

print("SBP-008 UI catalog integration verification: PASS")
