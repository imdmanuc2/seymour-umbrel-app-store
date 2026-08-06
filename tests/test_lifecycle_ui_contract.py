from pathlib import Path
repo=Path(__file__).resolve().parents[1]
app=repo/'seymour-blockchain-manager/data/web'
server=(app/'app.py').read_text();js=(app/'app.js').read_text();compose=(repo/'seymour-blockchain-manager/docker-compose.yml').read_text()
assert '/api/lifecycle/' in server
assert 'requiredConfirmation' in js
assert 'executeLifecycle' in js
assert 'LIFECYCLE_EVIDENCE_PATH' in compose
print('SBP-010 lifecycle UI contract verification: PASS')
