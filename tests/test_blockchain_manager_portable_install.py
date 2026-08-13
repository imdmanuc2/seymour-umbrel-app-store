from pathlib import Path

def test_portable_compose():
    compose = Path("seymour-blockchain-manager/docker-compose.yml").read_text()
    assert "/home/umbrel/seymour-umbrel-app-store-git/private/nexus-registration.env" not in compose
    assert "/home/umbrel/seymour-umbrel-app-store-git/scripts" not in compose
    assert "/home/umbrel/seymour-umbrel-app-store-git/shared" not in compose
    assert "${APP_DATA_DIR}/data/control:/control:ro" in compose
    assert "${APP_DATA_DIR}/data/shared:/seymour-platform/shared:ro" in compose
    assert "PYTHONPATH: /seymour-platform" in compose

def test_payload_exists():
    control = Path("seymour-blockchain-manager/data/control")
    for name in ("seymour-umbrel-app", "seymour-install-bch", "seymour-install-btc"):
        assert (control / name).is_file()
    assert Path("seymour-blockchain-manager/data/shared/blockchain_install").is_dir()
