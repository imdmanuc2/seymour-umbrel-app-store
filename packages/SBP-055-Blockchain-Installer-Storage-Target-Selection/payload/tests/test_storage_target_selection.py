from pathlib import Path

def test_contracts():
    app = Path("seymour-blockchain-manager/data/web/app.py").read_text()
    installer = Path("seymour-blockchain-manager/data/web/installer.py").read_text()
    js = Path("seymour-blockchain-manager/data/web/app.js").read_text()
    assert "/api/install/storage-targets" in app
    assert "storage_target_id: str" in installer
    assert 'data.get("storageTargetId"' in installer
    assert "preflight(value.storage_target_id)" in installer
    assert 'id="wizardStorageTarget"' in js
    assert "storageTargetId:" in js
