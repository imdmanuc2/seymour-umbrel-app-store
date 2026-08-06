from pathlib import Path


repo = Path(__file__).resolve().parents[1]
app = repo / "seymour-blockchain-manager"

required = [
    app / "umbrel-app.yml",
    app / "docker-compose.yml",
    app / "data" / "web" / "app.py",
    app / "data" / "web" / "index.html",
    app / "data" / "web" / "app.js",
    app / "data" / "web" / "style.css",
    app / "data" / "catalog" / "providers.v1.json",
]

for path in required:
    assert path.is_file(), path

html = (app / "data" / "web" / "index.html").read_text()
javascript = (app / "data" / "web" / "app.js").read_text()
stylesheet = (app / "data" / "web" / "style.css").read_text()
server = (app / "data" / "web" / "app.py").read_text()
compose = (app / "docker-compose.yml").read_text()

assert "Blockchain Manager" in html
assert 'id="providerGrid"' in html
assert "/api/providers" in javascript
assert "Coming soon" in javascript
assert "data-manage" in javascript
assert ".provider-grid" in stylesheet
assert "/api/health" in server
assert "/api/providers/" in server
assert "python:3.12-alpine" in compose
assert "APP_PORT: 8080" in compose

print("SBP-008 blockchain manager UI verification: PASS")
