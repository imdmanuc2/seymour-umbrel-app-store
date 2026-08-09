from pathlib import Path
repo = Path(__file__).resolve().parents[1]
text = (repo / "seymour-blockchain-manager/data/web/bch_runtime_probe.py").read_text()
assert "timeout: int = 8" in text
assert "timeout=8" in text
assert "timeout=25" in text
print("SBP-023 BCH sidecar observation contract verification: PASS")
