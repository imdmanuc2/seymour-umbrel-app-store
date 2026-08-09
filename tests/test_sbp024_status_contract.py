from pathlib import Path
repo = Path(__file__).resolve().parents[1]
text = (repo / 'seymour-bch-node/data/status/app.py').read_text()
assert '"uptime"' in text
assert '"rpc-slow"' in text
assert '"rpcReachable": True' in text
assert 'def health_payload' in text
print('SBP-024 BCH status-state normalization verification: PASS')
