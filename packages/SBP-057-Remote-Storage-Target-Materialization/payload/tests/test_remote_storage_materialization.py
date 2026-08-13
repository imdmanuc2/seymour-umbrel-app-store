from shared.blockchain_install.materialize import (
    build_nfs_plan,
    confirmation_token,
)

def test_nfs_plan():
    plan = build_nfs_plan(
        provider_id="bitcoin-mainnet",
        storage_host="192.168.1.155",
        storage_path="/mnt/umbrel-disk/seymour-data",
        runtime_host="192.168.1.154",
        runtime_mount_path="/mnt/seymour-storage",
    )
    assert plan.eligible is True
    assert plan.nfs_source == "192.168.1.155:/mnt/umbrel-disk/seymour-data"
    assert plan.data_path == "/mnt/seymour-storage/bitcoin-mainnet"
    assert plan.confirmation == "MATERIALIZE-bitcoin-mainnet-ON-192.168.1.155"

def test_unsafe_path_blocked():
    try:
        build_nfs_plan(
            provider_id="bitcoin-mainnet",
            storage_host="192.168.1.155",
            storage_path="/mnt/../etc",
            runtime_host="192.168.1.154",
            runtime_mount_path="/mnt/seymour-storage",
        )
    except ValueError:
        pass
    else:
        raise AssertionError("unsafe storage path accepted")
