from pathlib import Path

def test_unique_proxy_target():
    text = Path("seymour-blockchain-manager/docker-compose.yml").read_text()
    assert "APP_HOST: seymour-blockchain-manager-web" in text
    assert "APP_HOST: web" not in text
    assert "APP_PORT: 8080" in text
