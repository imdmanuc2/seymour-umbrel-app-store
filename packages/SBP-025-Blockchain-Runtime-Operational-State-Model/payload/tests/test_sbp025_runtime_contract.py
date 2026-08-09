from pathlib import Path
repo = Path(__file__).resolve().parents[2]
probe = (repo / "seymour-blockchain-manager/data/web/bch_runtime_probe.py").read_text()
integration = (repo / "seymour-blockchain-manager/data/web/nexus_integration.py").read_text()
assert "normalize_runtime_state" in probe
assert '"operationalState"' in probe
assert '"operationalState"' in integration
print("SBP-025 runtime integration contract verification: PASS")
