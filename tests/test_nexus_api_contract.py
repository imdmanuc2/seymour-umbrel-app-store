from pathlib import Path

repo = Path(__file__).resolve().parents[1]
web = repo / "seymour-blockchain-manager/data/web"

server = (web / "app.py").read_text()
compose = (repo / "seymour-blockchain-manager/docker-compose.yml").read_text()

assert "/api/nexus/discovery" in server
assert "/api/nexus/registration" in server
assert "registration_payload" in server
assert "append_registration_evidence" in server
assert "NEXUS_REGISTRATION_EVIDENCE_PATH" in compose

print("SBP-015 Nexus API contract verification: PASS")
