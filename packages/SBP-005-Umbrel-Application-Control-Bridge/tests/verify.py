from __future__ import annotations

import sys
import tempfile
from pathlib import Path

repo = Path(sys.argv[1]).resolve()
sys.path.insert(
    0,
    str(repo / "shared"),
)

from umbrel_control import UmbrelAppControlBridge


with tempfile.TemporaryDirectory() as temp:
    bridge = UmbrelAppControlBridge(
        helper_path=(
            repo
            / "shared"
            / "umbrel_control"
            / "native-client.ts"
        ),
        evidence_directory=Path(temp),
    )

    plan = bridge.execute(
        "install",
        "seymour-bch-node",
    )

    assert plan.mode == "plan"
    assert plan.executed is False
    assert plan.success is None
    assert (
        plan.result["requiredConfirmation"]
        == "INSTALL-seymour-bch-node"
    )
    assert plan.result["nativeApi"] is True
    assert (
        plan.result["directDockerLifecycle"]
        is False
    )

    try:
        bridge.execute(
            "install",
            "seymour-bch-node",
            execute=True,
            confirmation="WRONG",
        )
    except ValueError as exc:
        assert "Confirmation mismatch" in str(exc)
    else:
        raise AssertionError(
            "Incorrect confirmation was accepted."
        )

native = (
    repo
    / "shared"
    / "umbrel_control"
    / "native-client.ts"
).read_text()

assert "apps.install" in native
assert "apps.uninstall" in native
assert "apps.state" in native
assert "Authorization" in native
assert "docker compose" not in native.lower()

wrapper = (
    repo
    / "scripts"
    / "seymour-umbrel-app"
)
assert wrapper.is_file()
assert wrapper.stat().st_mode & 0o111

print(
    "SBP-005 Umbrel Application Control Bridge "
    "verification: PASS"
)
