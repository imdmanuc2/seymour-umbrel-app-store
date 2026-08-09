from pathlib import Path
repo = Path(__file__).resolve().parents[1]
text = (repo / "shared/umbrel_control/native-client.ts").read_text()
assert "apps.restart.mutate" in text
print("SBP-023 Umbrel native lifecycle client contract verification: PASS")
