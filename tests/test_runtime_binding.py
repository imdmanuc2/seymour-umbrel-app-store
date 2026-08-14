from pathlib import Path
from tempfile import TemporaryDirectory
from shared.blockchain_install.runtime_binding import persist_runtime_binding, verify_live_data_mount

def test_persist_and_verify():
    with TemporaryDirectory() as td:
        root=Path(td)
        compose=root/"docker-compose.yml"
        compose.write_text(
            "services:\n  node:\n    volumes:\n"
            "      - ${SEYMOUR_BLOCKCHAIN_DATA_PATH:-${APP_DATA_DIR}/data/node}:/data\n"
            "  status:\n    volumes:\n"
            "      - ${SEYMOUR_BLOCKCHAIN_DATA_PATH:-${APP_DATA_DIR}/data/node}:/node-data\n"
        )
        data=root/"chain"; data.mkdir()
        persist_runtime_binding(
            provider_id="bitcoin-cash-mainnet",
            app_id="seymour-bch-node",
            compose_path=compose,
            data_path=data,
        )
        text=compose.read_text()
        assert f"{data}:/data" in text
        assert f"{data}:/node-data" in text

    good=verify_live_data_mount(
        inspect_mounts=[{"Source":"/mnt/seymour-storage/bitcoin-cash-mainnet","Destination":"/data"}],
        expected_data_path=Path("/mnt/seymour-storage/bitcoin-cash-mainnet"),
    )
    assert good["healthy"]
