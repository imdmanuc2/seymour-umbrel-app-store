from pathlib import Path
from tempfile import TemporaryDirectory
from shared.blockchain_install.start_guard import resolve_storage_expectation

def test_unresolved_binding_blocks():
    with TemporaryDirectory() as td:
        root=Path(td)
        app=root/"app-data"/"seymour-bch-node"
        app.mkdir(parents=True)
        (app/"docker-compose.yml").write_text(
            "services:\n  node:\n    volumes:\n"
            "      - ${SEYMOUR_BLOCKCHAIN_DATA_PATH:-${APP_DATA_DIR}/data/node}:/data\n"
        )
        try:
            resolve_storage_expectation(data_directory=root, app_id="seymour-bch-node")
        except RuntimeError:
            return
        raise AssertionError("unresolved binding was not blocked")
