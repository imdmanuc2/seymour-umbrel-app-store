from pathlib import Path
import importlib.util
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
    "sbp016_retry",
    path,
)

module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

module.REGISTRATION_URL = (
    "https://nexus.example/api/registration"
)
module.REGISTRATION_TOKEN = "test-token"
module.MAX_ATTEMPTS = 3
module.BACKOFF_SECONDS = 0

attempts = []


def failing_opener(*args, **kwargs):
    attempts.append(1)
    raise OSError("temporary network failure")


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
        {
            "registrationId": (
                "registration-retry-test"
            ),
        },
        opener=failing_opener,
        sleep_fn=lambda _: None,
    )

    assert result.status == "failed"
    assert result.attempts == 3
    assert len(attempts) == 3
    assert "temporary network failure" in (
        result.error or ""
    )

print("SBP-016 retry and backoff verification: PASS")
