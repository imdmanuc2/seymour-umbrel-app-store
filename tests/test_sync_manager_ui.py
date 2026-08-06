from pathlib import Path
repo = Path(__file__).resolve().parents[1]
web = repo / "seymour-blockchain-manager/data/web"
server = (web / "app.py").read_text()
javascript = (web / "app.js").read_text()
stylesheet = (web / "style.css").read_text()
compose = (repo / "seymour-blockchain-manager/docker-compose.yml").read_text()
assert "/api/sync" in server
assert "showSyncManager" in javascript
assert "data-sync" in javascript
assert ".sync-kpis" in stylesheet
assert "SYNC_HISTORY_PATH" in compose
print("SBP-012 sync manager UI verification: PASS")
