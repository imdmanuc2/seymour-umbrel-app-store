from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from shared.blockchain_install.execution import (
    InstallResult,
)
from shared.blockchain_install.install_evidence import (
    CONTRACT,
    CONTRACT_VERSION,
    ProviderInstallEvidenceWriter,
)
from shared.blockchain_install.request import (
    InstallRequest,
)


def request(
    *,
    provider_id: str = (
        "bitcoin-mainnet"
    ),
    storage_target_id: str = (
        "storage-main"
    ),
) -> InstallRequest:
    return InstallRequest(
        provider_id=provider_id,
        storage_target_id=(
            storage_target_id
        ),
        app_id="seymour-bitcoin-node",
        node_name="Evidence Test Node",
        rpc_user="evidence-test",
        rpc_password="test-only-password",
        rpc_port=8332,
        p2p_port=8333,
        confirmation=(
            "INSTALL-seymour-bitcoin-node"
        ),
    )


def successful_result(
    *,
    operation_id: str = "op-1",
    storage_target_id: str = (
        "storage-main"
    ),
) -> InstallResult:
    return InstallResult(
        operation_id=operation_id,
        status="succeeded",
        result={
            "ignored": True,
        },
        verification={
            "verified": True,
            "evidence": {
                "state": {
                    "success": True,
                    "state": "running",
                },
                "storageTargetId": (
                    storage_target_id
                ),
                "bindingMode": "local",
                "runtimeDataMountMatches": (
                    True
                ),
                "runtimeBlocksMountMatches": (
                    True
                ),
                "requestedDataPath": (
                    "/private/data"
                ),
                "runtimeDataMountSource": (
                    "/private/data"
                ),
            },
            "error": None,
        },
        error=None,
    )


class ProviderInstallEvidenceTests(
    unittest.TestCase
):
    def setUp(self):
        self.temp = (
            tempfile.TemporaryDirectory()
        )
        self.root = Path(
            self.temp.name
        )
        self.writer = (
            ProviderInstallEvidenceWriter(
                umbrel_root=self.root
            )
        )

    def tearDown(self):
        self.temp.cleanup()

    def read(self, path):
        return json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

    def test_success_writes_history_and_provider_current(self):
        payload = self.writer.write(
            request=request(),
            result=successful_result(),
        )

        history = (
            self.writer.paths.history
            / "op-1.json"
        )

        current = (
            self.writer.paths.current
            / "bitcoin-mainnet.json"
        )

        self.assertTrue(
            history.is_file()
        )
        self.assertTrue(
            current.is_file()
        )

        self.assertEqual(
            self.read(history),
            self.read(current),
        )

        self.assertEqual(
            payload["contract"],
            CONTRACT,
        )
        self.assertEqual(
            payload["version"],
            CONTRACT_VERSION,
        )
        self.assertEqual(
            payload["providerId"],
            "bitcoin-mainnet",
        )
        self.assertEqual(
            payload["storageTargetId"],
            "storage-main",
        )
        self.assertEqual(
            payload["status"],
            "installed",
        )
        self.assertTrue(
            payload["verified"]
        )

    def test_failed_result_writes_history_only(self):
        result = InstallResult(
            operation_id="op-failed",
            status="failed",
            verification=None,
            error="install failed",
        )

        payload = self.writer.write(
            request=request(),
            result=result,
        )

        self.assertEqual(
            payload["status"],
            "failed",
        )

        self.assertTrue(
            (
                self.writer.paths.history
                / "op-failed.json"
            ).is_file()
        )

        self.assertFalse(
            (
                self.writer.paths.current
                / "bitcoin-mainnet.json"
            ).exists()
        )

    def test_failed_reinstall_preserves_last_known_good_current(self):
        self.writer.write(
            request=request(),
            result=successful_result(
                operation_id="op-good"
            ),
        )

        current = (
            self.writer.paths.current
            / "bitcoin-mainnet.json"
        )

        before = self.read(
            current
        )

        failed = InstallResult(
            operation_id="op-bad",
            status="failed",
            verification={
                "verified": False,
                "evidence": {},
                "error": (
                    "state verification failed"
                ),
            },
            error=None,
        )

        self.writer.write(
            request=request(),
            result=failed,
        )

        after = self.read(
            current
        )

        self.assertEqual(
            before,
            after,
        )

        self.assertTrue(
            (
                self.writer.paths.history
                / "op-bad.json"
            ).is_file()
        )

    def test_verified_storage_target_must_match_request(self):
        with self.assertRaisesRegex(
            ValueError,
            "storage target identity mismatch",
        ):
            self.writer.write(
                request=request(),
                result=successful_result(
                    storage_target_id=(
                        "wrong-storage"
                    )
                ),
            )

    def test_unverified_result_cannot_be_current(self):
        result = InstallResult(
            operation_id="op-unverified",
            status="succeeded",
            verification={
                "verified": False,
                "evidence": {
                    "state": {
                        "success": True,
                    },
                    "storageTargetId": (
                        "storage-main"
                    ),
                    "runtimeDataMountMatches": (
                        True
                    ),
                    "runtimeBlocksMountMatches": (
                        True
                    ),
                },
                "error": "not verified",
            },
        )

        payload = self.writer.write(
            request=request(),
            result=result,
        )

        self.assertEqual(
            payload["status"],
            "failed",
        )

        self.assertFalse(
            (
                self.writer.paths.current
                / "bitcoin-mainnet.json"
            ).exists()
        )

    def test_state_failure_cannot_be_current(self):
        result = successful_result(
            operation_id="op-state"
        )

        verification = dict(
            result.verification
        )

        evidence = dict(
            verification["evidence"]
        )

        evidence["state"] = {
            "success": False,
        }

        verification[
            "evidence"
        ] = evidence

        result = InstallResult(
            operation_id=result.operation_id,
            status=result.status,
            result=result.result,
            verification=verification,
            error=result.error,
        )

        payload = self.writer.write(
            request=request(),
            result=result,
        )

        self.assertEqual(
            payload["status"],
            "failed",
        )

    def test_data_mount_failure_cannot_be_current(self):
        result = successful_result(
            operation_id="op-data"
        )

        verification = dict(
            result.verification
        )

        evidence = dict(
            verification["evidence"]
        )

        evidence[
            "runtimeDataMountMatches"
        ] = False

        verification[
            "evidence"
        ] = evidence

        result = InstallResult(
            operation_id=result.operation_id,
            status=result.status,
            verification=verification,
        )

        payload = self.writer.write(
            request=request(),
            result=result,
        )

        self.assertEqual(
            payload["status"],
            "failed",
        )

    def test_blocks_mount_failure_cannot_be_current(self):
        result = successful_result(
            operation_id="op-blocks"
        )

        verification = dict(
            result.verification
        )

        evidence = dict(
            verification["evidence"]
        )

        evidence[
            "runtimeBlocksMountMatches"
        ] = False

        verification[
            "evidence"
        ] = evidence

        result = InstallResult(
            operation_id=result.operation_id,
            status=result.status,
            verification=verification,
        )

        payload = self.writer.write(
            request=request(),
            result=result,
        )

        self.assertEqual(
            payload["status"],
            "failed",
        )

    def test_durable_evidence_excludes_paths_state_and_result(self):
        payload = self.writer.write(
            request=request(),
            result=successful_result(),
        )

        encoded = json.dumps(
            payload
        )

        self.assertNotIn(
            "/private/data",
            encoded,
        )
        self.assertNotIn(
            '"state"',
            encoded,
        )
        self.assertNotIn(
            '"result"',
            encoded,
        )

    def test_provider_current_is_independent_per_provider(self):
        self.writer.write(
            request=request(),
            result=successful_result(
                operation_id="op-btc"
            ),
        )

        monero_request = request(
            provider_id="monero-mainnet",
        )

        monero_result = (
            successful_result(
                operation_id="op-xmr"
            )
        )

        self.writer.write(
            request=monero_request,
            result=monero_result,
        )

        self.assertTrue(
            (
                self.writer.paths.current
                / "bitcoin-mainnet.json"
            ).is_file()
        )

        self.assertTrue(
            (
                self.writer.paths.current
                / "monero-mainnet.json"
            ).is_file()
        )


if __name__ == "__main__":
    unittest.main()
