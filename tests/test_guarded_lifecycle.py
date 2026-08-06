from pathlib import Path
from tempfile import TemporaryDirectory
import importlib.util,sys
repo=Path(__file__).resolve().parents[1]
path=repo/'seymour-blockchain-manager/data/web/lifecycle.py'
spec=importlib.util.spec_from_file_location('sbp010_lifecycle',path);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
assert m.confirmation_token(m.LifecycleAction.START,'seymour-bch-node')=='START-seymour-bch-node'
with TemporaryDirectory() as d:
 root=Path(d);fake=root/'control';evidence=root/'evidence.jsonl'
 fake.write_text('#!/usr/bin/env python3\nimport json,sys\nprint(json.dumps({"success":True,"result":{"state":"ready","progress":0}}))\n');fake.chmod(0o755)
 s=m.GuardedLifecycleService(fake,m.LifecycleEvidenceStore(evidence))
 bad=s.execute('bitcoin-cash-mainnet','seymour-bch-node',m.LifecycleAction.RESTART,'WRONG');assert bad.status.value=='failed' and not bad.executed
 ok=s.execute('bitcoin-cash-mainnet','seymour-bch-node',m.LifecycleAction.RESTART,'RESTART-seymour-bch-node');assert ok.status.value=='succeeded' and ok.executed
 assert evidence.is_file()
print('SBP-010 guarded lifecycle verification: PASS')
