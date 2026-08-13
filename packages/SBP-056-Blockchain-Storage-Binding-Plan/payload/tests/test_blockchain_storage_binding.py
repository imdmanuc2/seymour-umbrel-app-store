from shared.blockchain_install.binding import (
    build_binding_plan,
    provider_storage_name,
)
from shared.blockchain_install.models import StorageTarget, StorageTargetType


def target(
    *,
    kind=StorageTargetType.ATTACHED,
    path="/mnt/umbrel-disk",
    writable=True,
    reachable=True,
    persistent=True,
    remote_host=None,
):
    return StorageTarget(
        target_id="target-test",
        target_type=kind,
        host="storage-host",
        path=path,
        filesystem="ext4" if kind != StorageTargetType.REMOTE else "nfs4",
        source="/dev/sdb1" if kind != StorageTargetType.REMOTE else "192.168.1.155:/storage",
        total_bytes=5_500_000_000_000,
        used_bytes=100_000_000_000,
        free_bytes=5_400_000_000_000,
        writable=writable,
        persistent=persistent,
        reachable=reachable,
        mount_point=path,
        remote_host=remote_host,
    )


def test_attached_plan():
    plan = build_binding_plan(
        provider_id="bitcoin-mainnet",
        runtime_host="192.168.1.154",
        storage_target=target(),
    )
    assert plan.eligible is True
    assert plan.data_path == "/mnt/umbrel-disk/seymour-data/bitcoin-mainnet"


def test_remote_plan():
    plan = build_binding_plan(
        provider_id="bitcoin-mainnet",
        runtime_host="192.168.1.154",
        storage_target=target(
            kind=StorageTargetType.REMOTE,
            path="/mnt/seymour-remote",
            remote_host="192.168.1.155",
        ),
    )
    assert plan.storage_type == "remote"
    assert plan.remote_host == "192.168.1.155"
    assert plan.data_path == "/mnt/seymour-remote/seymour-data/bitcoin-mainnet"


def test_unwritable_target_blocked():
    plan = build_binding_plan(
        provider_id="bitcoin-mainnet",
        runtime_host="umbrel",
        storage_target=target(writable=False),
    )
    assert plan.eligible is False
    assert plan.errors


def test_provider_name_rejects_unsafe_path():
    try:
        provider_storage_name("../bitcoin")
    except ValueError:
        pass
    else:
        raise AssertionError("unsafe provider path accepted")
