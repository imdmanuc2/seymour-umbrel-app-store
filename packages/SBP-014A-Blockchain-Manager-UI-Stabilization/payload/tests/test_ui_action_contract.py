from pathlib import Path

repo = Path(__file__).resolve().parents[1]
web = repo / "seymour-blockchain-manager/data/web"

javascript = (web / "app.js").read_text()
stylesheet = (web / "style.css").read_text()
server = (web / "app.py").read_text()

contracts = (
    ('data-sync="${provider.providerId}"', "showSyncManager", "/api/sync"),
    ('data-adopt="${provider.providerId}"', "showAdoptionWizard", "/api/adoption/plan"),
    ('data-operations="${provider.providerId}"', "showOperationsCenter", "/api/operations/diagnostics"),
    ('data-manage="${provider.providerId}"', "showManage", "/api/lifecycle/"),
)

for button, function, route in contracts:
    assert button in javascript
    assert function in javascript
    assert route in server

assert ".operations-actions" in stylesheet
assert ".adoption-label" in stylesheet
assert ".sync-kpis" in stylesheet
assert ".lifecycle-actions" in stylesheet

print("SBP-014A UI action contract verification: PASS")
