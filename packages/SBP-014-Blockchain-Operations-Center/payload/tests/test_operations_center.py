from pathlib import Path
import importlib.util,sys,tempfile
repo=Path(__file__).resolve().parents[1];path=repo/"seymour-blockchain-manager/data/web/operations_center.py"
spec=importlib.util.spec_from_file_location("sbp014_ops",path);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
assert m.confirmation_token(m.OperationKind.BACKUP)=="BACKUP-seymour-bch-node"
with tempfile.TemporaryDirectory() as d:
 m.EVIDENCE_PATH=Path(d)/"operations.jsonl";m.HEALTH_HISTORY_PATH=Path(d)/"health.jsonl";m.BACKUP_ROOT=Path(d)/"backups"
 p=m.plan(m.OperationKind.BACKUP,{"reason":"test"});assert p.status.value=="planned"
 r=m.execute_backup("WRONG");assert r.status.value=="failed";assert m.EVIDENCE_PATH.is_file()
print("SBP-014 operations center verification: PASS")
