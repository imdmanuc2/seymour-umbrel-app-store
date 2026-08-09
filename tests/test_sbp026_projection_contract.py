from pathlib import Path

repo = Path(__file__).resolve().parents[1]
text = (
    repo
    / "seymour-blockchain-manager"
    / "data"
    / "web"
    / "nexus_integration.py"
).read_text()

required = [
    'telemetry["operationalStateName"]',
    'telemetry["runtimeState"]',
    'telemetry["runtimeStateReason"]',
    'telemetry["runtimeRpcReachable"]',
    'telemetry["runtimeRpcHealthy"]',
    'telemetry["runtimeInitialBlockDownload"]',
    'telemetry["runtimeVerificationProgress"]',
    'asset["runtimeState"]',
]

for marker in required:
    assert marker in text, marker

print("SBP-026 Nexus runtime-state projection contract verification: PASS")
