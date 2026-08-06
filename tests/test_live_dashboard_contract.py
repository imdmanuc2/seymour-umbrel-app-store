import importlib.util
from pathlib import Path


repo = Path(__file__).resolve().parents[1]
path = (
    repo
    / "seymour-blockchain-manager"
    / "data"
    / "web"
    / "telemetry.py"
)

spec = importlib.util.spec_from_file_location(
    "sbp009_telemetry",
    path,
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

host = module.host_telemetry()

assert "architecture" in host
assert "cpuPercent" in host
assert "memory" in host
assert "storage" in host
assert "docker" in host

status = module.normalized_sync({
    "blocks": 50,
    "headers": 100,
})

assert status["height"] == 50
assert status["headers"] == 100
assert status["progressPercent"] == 50.0

payload = module.dashboard_payload()

assert "generatedAt" in payload
assert "host" in payload
assert "providers" in payload
assert "bitcoin-cash-mainnet" in payload["providers"]

print("SBP-009 telemetry contract verification: PASS")
