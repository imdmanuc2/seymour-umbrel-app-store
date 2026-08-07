from pathlib import Path
repo=Path(__file__).resolve().parents[1]
a=(repo/"seymour-blockchain-manager/data/web/app.py").read_text(); c=(repo/"seymour-blockchain-manager/docker-compose.yml").read_text()
assert "/api/nexus/scheduler/status" in a
assert "/api/nexus/scheduler/run" in a
assert "start_nexus_scheduler()" in a
assert "NEXUS_REFRESH_ENABLED" in c
assert "NEXUS_REFRESH_INTERVAL_SECONDS" in c
print("SBP-019 scheduler integration contract verification: PASS")
