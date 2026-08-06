from pathlib import Path
import importlib.util
import sys
import tempfile

repo = Path(__file__).resolve().parents[1]
path = repo / "seymour-blockchain-manager/data/web/adoption.py"
spec = importlib.util.spec_from_file_location("sbp013_adoption", path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    source = root / "source"
    destination = root / "managed"
    (source / "blocks").mkdir(parents=True)
    (source / "chainstate").mkdir()
    (source / "blocks" / "blk00000.dat").write_text("block")
    (source / "chainstate" / "state.dat").write_text("state")
    service = module.AdoptionService(
        destination=destination,
        evidence_path=root / "evidence.jsonl",
        plans_path=root / "plans",
    )
    plan = service.plan(source)
    assert plan.validation["source"]["valid"] is True
    rejected = service.execute(plan.operation_id, "WRONG")
    assert rejected.status.value == "failed"
    plan2 = service.plan(source)
    adopted = service.execute(plan2.operation_id, "ADOPT-seymour-bch-node")
    assert adopted.status.value == "succeeded"
    assert (destination / "blocks").is_dir()

print("SBP-013 existing node adoption verification: PASS")
