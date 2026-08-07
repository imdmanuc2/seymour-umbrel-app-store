from pathlib import Path
import importlib.util
import json
import sys
import tempfile


repo = Path(__file__).resolve().parents[1]

path = (
    repo
    / "seymour-blockchain-manager"
    / "data"
    / "web"
    / "nexus_delivery.py"
)

spec = importlib.util.spec_from_file_location(
    "sbp016_delivery",
    path,
)

module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

payload = {
    "registrationId": "registration-test",
    "document": {
        "schemaVersion": 1,
    },
}

assert module.delivery_id(
    "registration-test"
).startswith("nexus-delivery-")

assert module.idempotency_key(
    "registration-test"
) == "seymour-registration-registration-test"

with tempfile.TemporaryDirectory() as directory:
    module.EVIDENCE_PATH = (
        Path(directory)
        / "delivery.jsonl"
    )

    module.STATUS_PATH = (
        Path(directory)
        / "status.json"
    )

    result = module.deliver(
        payload,
        dry_run=True,
    )

    assert result.status == "dry-run"
    assert result.attempts == 0
    assert module.EVIDENCE_PATH.is_file()
    assert module.STATUS_PATH.is_file()

    status = module.load_status()

    assert status["registration_id"] == (
        "registration-test"
    )

print("SBP-016 Nexus delivery verification: PASS")
