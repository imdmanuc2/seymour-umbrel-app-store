import json,sys
from pathlib import Path
repo=Path(sys.argv[1]);app=repo/'seymour-bch-node'
for r in ('umbrel-app.yml','docker-compose.yml','data/node/entrypoint.sh','data/status/Dockerfile','data/status/app.py','data/status/index.html','data/contracts/bitcoin-cash-node.json','data/provisioning/modes.json'):assert (app/r).is_file(),r
m=(app/'umbrel-app.yml').read_text();c=(app/'docker-compose.yml').read_text();e=(app/'data/node/entrypoint.sh').read_text()
assert 'id: seymour-bch-node' in m and 'version: "0.2.0-alpha"' in m
assert 'bitcoin-cash-node:latest' in c and '${APP_DATA_DIR}/data/node:/data' in c
assert 'zmqpubrawblock' in e and 'zmqpubrawtx' in e
assert json.loads((app/'data/contracts/bitcoin-cash-node.json').read_text())['service']['network']=='bitcoin-cash-mainnet'
assert len(json.loads((app/'data/provisioning/modes.json').read_text())['modes'])==4
print('SBP-001 Bitcoin Cash Node foundation verification: PASS')
