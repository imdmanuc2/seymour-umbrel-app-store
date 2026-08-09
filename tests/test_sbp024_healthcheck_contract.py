from pathlib import Path
repo = Path(__file__).resolve().parents[1]
text = (repo / 'seymour-bch-node/docker-compose.yml').read_text()
start = text.find('healthcheck:')
end = text.find('volumes:', start)
block = text[start:end]
assert 'uptime 2>&1' in block
assert 'grep -qi "server in warmup"' in block
assert 'exit "$$rc"' in block
assert 'getblockchaininfo' not in block
print('SBP-024 BCH warmup healthcheck contract verification: PASS')
