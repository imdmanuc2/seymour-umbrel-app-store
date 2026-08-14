from pathlib import Path
from tempfile import TemporaryDirectory
from shared.blockchain_recovery import plan,warmup_finding,RecoveryState
def test_warmup():
    assert warmup_finding("error code: -28\nVerifying blocks...").state==RecoveryState.RECOVERING
def test_missing_storage():
    with TemporaryDirectory() as td:
        r=plan("bitcoin-cash-mainnet","test",storage_target=str(Path(td)/"missing"))
        assert r.state==RecoveryState.BLOCKED
