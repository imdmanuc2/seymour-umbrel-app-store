from pathlib import Path
repo = Path(__file__).resolve().parents[1]
web = repo / "seymour-blockchain-manager/data/web"
server = (web / "app.py").read_text()
javascript = (web / "app.js").read_text()
stylesheet = (web / "style.css").read_text()
compose = (repo / "seymour-blockchain-manager/docker-compose.yml").read_text()
assert "/api/install/preflight" in server
assert "/api/install/credentials" in server
assert "/api/install/execute" in server
assert "openInstallWizard" in javascript
assert "wizardInstall" in javascript
assert ".wizard-steps" in stylesheet
assert "SEYMOUR_BCH_INSTALL_SCRIPT" in compose
assert "INSTALL_EVIDENCE_PATH" in compose
print("SBP-011 installation wizard UI verification: PASS")
