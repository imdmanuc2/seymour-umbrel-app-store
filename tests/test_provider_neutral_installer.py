from pathlib import Path

def test_provider_neutral_contracts():
    installer = Path("seymour-blockchain-manager/data/web/installer.py").read_text()
    ui = Path("seymour-blockchain-manager/data/web/app.js").read_text()
    assert '"bitcoin-mainnet"' in installer
    assert '"bitcoin-cash-mainnet"' in installer
    assert '"seymour-bitcoin-node"' in installer
    assert '"seymour-bch-node"' in installer
    assert 'provider_runtime(value.provider_id)' in installer
    assert 'runtime["installScript"]' in installer
    assert 'runtime["appId"]' in installer
    assert 'f"{prefix}_RPC_USER"' in installer
    assert 'Install ${provider.displayName}' in ui
    assert 'Seymour ${provider.displayName} Node' in ui
