from pathlib import Path
from tempfile import TemporaryDirectory
from shared.blockchain_install.models import StorageTarget, StorageTargetType
from shared.blockchain_install.storage import verify_storage_target

def test_attached_directory_without_mount_fails_closed():
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "missing-external-disk"
        path.mkdir()
        target = StorageTarget(
            target_id="attached-test", target_type=StorageTargetType.ATTACHED,
            host="test", path=str(path), filesystem="ext4", source="/dev/sdz1",
            total_bytes=1, used_bytes=0, free_bytes=1, writable=True,
            persistent=True, reachable=True, mount_point=str(path),
            filesystem_uuid="definitely-not-real",
        )
        result = verify_storage_target(target)
        assert result["healthy"] is False
        assert result["isMountPoint"] is False
