from pathlib import Path
repo = Path(__file__).resolve().parents[1]
web = repo / "seymour-blockchain-manager/data/web"
server = (web / "app.py").read_text()
compose = (repo / "seymour-blockchain-manager/docker-compose.yml").read_text()
assert "/api/adoption/plan" in server
assert "/api/adoption/execute" in server
assert "ADOPTION_EVIDENCE_PATH" in compose
print("SBP-013 adoption UI verification: PASS")
