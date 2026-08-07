from pathlib import Path
r=Path(__file__).resolve().parents[1];w=r/"seymour-blockchain-manager/data/web"
a=(w/"app.py").read_text();j=(w/"app.js").read_text();c=(w/"style.css").read_text();d=(r/"seymour-blockchain-manager/docker-compose.yml").read_text()
assert "/api/operations/diagnostics" in a and "/api/operations/plan" in a and "/api/operations/backup" in a
assert "showOperationsCenter" in j and "data-operations" in j and ".operations-actions" in c and "OPERATIONS_EVIDENCE_PATH" in d
print("SBP-014 operations center UI verification: PASS")
