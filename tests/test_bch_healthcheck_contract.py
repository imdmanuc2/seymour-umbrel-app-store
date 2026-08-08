from pathlib import Path
repo = Path(__file__).resolve().parents[1]
legacy = []
for path in (repo / "seymour-bch-node").rglob("*"):
    if not path.is_file():
        continue
    try:
        text = path.read_text()
    except Exception:
        continue
    if "rpcwaittimeout=5 getblockchaininfo" in text:
        legacy.append(str(path))
assert not legacy, "Legacy expensive BCH healthcheck remains in: " + ", ".join(legacy)
print("SBP-022 lightweight BCH healthcheck verification: PASS")
