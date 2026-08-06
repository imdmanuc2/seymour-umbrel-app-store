from pathlib import Path


repo = Path(__file__).resolve().parents[1]
web = (
    repo
    / "seymour-blockchain-manager"
    / "data"
    / "web"
)

required = [
    web / "telemetry.py",
    web / "app.py",
    web / "index.html",
    web / "app.js",
    web / "style.css",
]

for path in required:
    assert path.is_file(), path

telemetry = (web / "telemetry.py").read_text()
server = (web / "app.py").read_text()
html = (web / "index.html").read_text()
javascript = (web / "app.js").read_text()
stylesheet = (web / "style.css").read_text()

assert "host_telemetry" in telemetry
assert "bch_telemetry" in telemetry
assert "docker_container" in telemetry
assert "normalized_sync" in telemetry
assert "/api/dashboard" in server
assert 'id="hostPanel"' in html
assert "setInterval(refreshTelemetry, 5000)" in javascript
assert "progressBar" in javascript
assert ".progress" in stylesheet

print("SBP-009 live dashboard source verification: PASS")
