from pathlib import Path


repo = Path(__file__).resolve().parents[1]

web = (
    repo
    / "seymour-blockchain-manager"
    / "data"
    / "web"
)

server = (web / "app.py").read_text()

compose = (
    repo
    / "seymour-blockchain-manager"
    / "docker-compose.yml"
).read_text()

assert "/api/nexus/delivery/status" in server
assert "/api/nexus/delivery" in server
assert "/api/nexus/delivery" in server
assert "deliver(" in server
assert "NEXUS_REGISTRATION_URL" in compose
assert "NEXUS_REGISTRATION_TOKEN" in compose
assert "NEXUS_DELIVERY_EVIDENCE_PATH" in compose

print("SBP-016 Nexus delivery API verification: PASS")
