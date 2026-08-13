from pathlib import Path
from shared.blockchain_install import HostProfile, StorageTarget, StorageTargetType, capacity_policy, evaluate, probe_writable, target_from_path

def provider():
    return {"providerId":"bitcoin-mainnet","supportedArchitectures":["amd64","arm64"],"estimatedDiskBytes":800_000_000_000}

def host():
    return HostProfile("umbrel-test","amd64",4,8_000_000_000,True,True)

def test_capacity_reserve():
    p = capacity_policy(800_000_000_000)
    assert p.reserve_bytes == 160_000_000_000
    assert p.required_bytes == 960_000_000_000

def test_remote_target_accepted():
    t = StorageTarget("remote-test",StorageTargetType.REMOTE,"umbrel-test","/mnt/seymour-btc","nfs4","192.168.1.155:/btc",5_500_000_000_000,200_000_000_000,5_300_000_000_000,True,True,True,"/mnt/seymour-btc","192.168.1.155")
    r = evaluate(provider=provider(),host=host(),storage_target=t)
    assert r.compatible is True
    assert r.storage_target["type"] == "remote"

def test_insufficient_storage_blocked():
    t = StorageTarget("local-test",StorageTargetType.LOCAL,"umbrel-test","/data","ext4","/dev/sda",1_000_000_000_000,200_000_000_000,800_000_000_000,True,True,True)
    r = evaluate(provider=provider(),host=host(),storage_target=t)
    assert r.compatible is False
    assert r.checks["storageCapacityHealthy"] is False

def test_unsupported_arch_blocked():
    h = HostProfile("test","riscv64",4,8_000_000_000,True,True)
    t = StorageTarget("t",StorageTargetType.LOCAL,"test","/data","ext4","/dev/sda",2_000_000_000_000,0,2_000_000_000_000,True,True,True)
    r = evaluate(provider=provider(),host=h,storage_target=t)
    assert r.compatible is False

def test_write_probe(tmp_path: Path):
    assert probe_writable(tmp_path)
    t = target_from_path(tmp_path,target_type=StorageTargetType.ATTACHED,filesystem="ext4",source="/dev/test",check_writable=True)
    assert t.writable
    assert t.free_bytes > 0
