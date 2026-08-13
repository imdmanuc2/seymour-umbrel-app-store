from pathlib import Path

def test_contracts():
    btc = Path("seymour-bitcoin-node/docker-compose.yml").read_text()
    bch = Path("seymour-bch-node/docker-compose.yml").read_text()
    installer = Path("seymour-blockchain-manager/data/web/installer.py").read_text()
    assert "${SEYMOUR_BLOCKCHAIN_DATA_PATH:-${APP_DATA_DIR}/data/node}:/data" in btc
    assert "${SEYMOUR_BLOCKCHAIN_DATA_PATH:-${APP_DATA_DIR}/data/node}:/node-data:ro" in btc
    assert "${SEYMOUR_BLOCKCHAIN_DATA_PATH:-${APP_DATA_DIR}/data/node}:/data" in bch
    assert "${SEYMOUR_BLOCKCHAIN_DATA_PATH:-${APP_DATA_DIR}/data/node}:/node-data" in bch
    assert "build_binding_plan(" in installer
    assert '"SEYMOUR_BLOCKCHAIN_DATA_PATH": str(data_path)' in installer
    assert '"runtimeDataMountMatches": mount_matches' in installer
