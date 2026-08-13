from pathlib import Path
import json

def test_bitcoin_provider_activation():
    for catalog in (
        Path("shared/provider_catalog/providers.v1.json"),
        Path("seymour-blockchain-manager/data/catalog/providers.v1.json"),
    ):
        data = json.loads(catalog.read_text())
        btc = next(x for x in data["providers"] if x["providerId"] == "bitcoin-mainnet")
        assert btc["availability"] == "live"
        assert btc["selectable"] is True
        assert btc["productionImage"] == "ghcr.io/imdmanuc2/seymour-bitcoin-node:29.0.0"
        assert btc["installAction"]["appId"] == "seymour-bitcoin-node"

def test_provider_specific_preflight():
    app = Path("seymour-blockchain-manager/data/web/app.py").read_text()
    js = Path("seymour-blockchain-manager/data/web/app.js").read_text()
    assert 'provider_id=provider_id' in app
    assert '/api/install/preflight?providerId=' in js
