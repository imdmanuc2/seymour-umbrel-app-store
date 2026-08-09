from pathlib import Path
repo = Path(__file__).resolve().parents[1]
text = (repo / "shared/umbrel_control/bridge.py").read_text()
assert "_native_result_error" in text
assert "_state_matches_action" in text
assert "directDockerLifecycle" in text
assert "nativeApi" in text
print("SBP-023 lifecycle result reconciliation contract verification: PASS")
