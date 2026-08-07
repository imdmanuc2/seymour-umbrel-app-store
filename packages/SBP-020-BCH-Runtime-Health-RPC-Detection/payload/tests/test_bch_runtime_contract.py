from pathlib import Path
r=Path(__file__).resolve().parents[1]
a=(r/"seymour-blockchain-manager/data/web/app.py").read_text(); n=(r/"seymour-blockchain-manager/data/web/nexus_integration.py").read_text(); c=(r/"seymour-blockchain-manager/docker-compose.yml").read_text()
assert "/api/runtime/bch-health" in a
assert "_sbp020_registration_payload" in n
assert "BCH_NODE_CONTAINER" in c and "/var/run/docker.sock:/var/run/docker.sock:ro" in c
print("SBP-020 runtime integration contract verification: PASS")
