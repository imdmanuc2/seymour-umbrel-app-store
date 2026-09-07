from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from shared.blockchain_install import (
    InstallRequest,
    UmbrelCommandResult,
    UmbrelProviderControl,
    UmbrelTargetInstallAdapter,
)
from shared.blockchain_install.models import (
    StorageTarget,
    StorageTargetType,
)
from shared.blockchain_install.runtime_binding import (
    RuntimeBindingMode,
)


def request(
    *,
    provider_id="bitcoin-mainnet",
    app_id="seymour-bitcoin-node",
    storage_target_id="storage-local",
    rpc_port=8332,
    p2p_port=8333,
):
    return InstallRequest.from_dict({
        "providerId": provider_id,
        "appId": app_id,
        "nodeName": "Test Node",
        "rpcUser": "seymour_rpc",
        "rpcPassword": "x" * 32,
        "rpcPort": rpc_port,
        "p2pPort": p2p_port,
        "storageTargetId":
            storage_target_id,
        "confirmation":
            f"INSTALL-{app_id}",
    })


def provider(
    *,
    estimated_disk_bytes=800_000_000_000,
):
    return {
        "estimatedDiskBytes":
            estimated_disk_bytes,
    }


def target(
    *,
    target_id="storage-local",
    target_type=StorageTargetType.LOCAL,
    path="/tmp/seymour-target",
):
    return StorageTarget(
        target_id=target_id,
        target_type=target_type,
        host="umbrel-test",
        path=path,
        filesystem="ext4",
        source="/dev/test",
        total_bytes=10_000,
        used_bytes=1_000,
        free_bytes=9_000,
        writable=True,
        persistent=True,
        reachable=True,
        mount_point=path,
        remote_host=(
            "storage-test"
            if (
                target_type
                == StorageTargetType.REMOTE
            )
            else None
        ),
        filesystem_uuid=None,
    )


class Fixture:
    def __init__(
        self,
        *,
        storage_target=None,
        storage_healthy=True,
        runner_code=0,
    ):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.storage_target = (
            storage_target
            if storage_target is not None
            else target(
                path=str(
                    self.root
                    / "storage"
                )
            )
        )

        self.storage_healthy = (
            storage_healthy
        )
        self.runner_code = runner_code

        self.runner_calls = []
        self.verifier_calls = []
        self.prepared = []
        self.handoff_calls = []
        self.mounts = []
        self.state = {
            "success": True,
            "payload": {
                "state": "running",
            },
        }

        self.controls = {
            "bitcoin-mainnet":
                UmbrelProviderControl(
                    install_script=(
                        self.root
                        / "seymour-install-btc"
                    ),
                    rpc_prefix="BTC",
                ),
            "bitcoin-cash-mainnet":
                UmbrelProviderControl(
                    install_script=(
                        self.root
                        / "seymour-install-bch"
                    ),
                    rpc_prefix="BCH",
                ),
            "monero-mainnet":
                UmbrelProviderControl(
                    install_script=(
                        self.root
                        / "seymour-install-monero"
                    ),
                    rpc_prefix="XMR",
                ),
        }

        for value in self.controls.values():
            value.install_script.write_text(
                "#!/bin/sh\n"
            )

    def close(self):
        self.tmp.cleanup()

    def resolver(self, target_id):
        if (
            self.storage_target
            and target_id
            == self.storage_target.target_id
        ):
            return self.storage_target

        return None

    def verifier(self, value, **kwargs):
        self.verifier_calls.append({
            "value": value,
            "kwargs": dict(kwargs),
        })

        return {
            "healthy":
                self.storage_healthy,
            "targetId":
                value.target_id,
            "errors": (
                []
                if self.storage_healthy
                else ["mount mismatch"]
            ),
            "dataPath":
                str(
                    kwargs.get("data_path")
                ),
        }

    def preparer(self, binding):
        self.prepared.append(binding)

        return {
            "mode":
                binding.mode.value,
        }

    def handoff(
        self,
        *,
        binding_path,
        data_directory,
        app_id,
    ):
        call = {
            "binding_path": Path(binding_path),
            "data_directory": Path(data_directory),
            "app_id": app_id,
        }
        self.handoff_calls.append(call)

        return {
            "appId": app_id,
            "bindingFile": str(
                Path(data_directory)
                / "app-data"
                / app_id
                / "data"
                / "runtime-binding.env"
            ),
            "staged": True,
        }

    def runner(
        self,
        command,
        env,
        timeout,
    ):
        self.runner_calls.append({
            "command": list(command),
            "env": dict(env),
            "timeout": timeout,
        })

        return UmbrelCommandResult(
            return_code=self.runner_code,
            stdout=(
                '{"success": true}'
                if self.runner_code == 0
                else ""
            ),
            stderr=(
                ""
                if self.runner_code == 0
                else "install failed"
            ),
        )

    def adapter(self):
        return UmbrelTargetInstallAdapter(
            provider_controls=self.controls,
            storage_resolver=self.resolver,
            storage_verifier=self.verifier,
            storage_preparer=self.preparer,
            command_runner=self.runner,
            state_reader=(
                lambda app_id:
                    dict(self.state)
            ),
            mount_inspector=(
                lambda app_id:
                    list(self.mounts)
            ),
            script_available=(
                lambda path:
                    path.is_file()
            ),
            runtime_host="umbrel-test",
            binding_config_root=(
                self.root
                / "bindings"
            ),
            umbrel_data_directory=(
                self.root
                / "umbrel"
            ),
            bch_local_data_path=(
                self.root
                / "umbrel-app-data"
                / "seymour-bch-node"
                / "data"
                / "node"
            ),
            binding_handoff=self.handoff,
            environment_provider=(
                lambda: {
                    "PATH": "/usr/bin",
                }
            ),
        )


class UmbrelTargetInstallAdapterTests(
    unittest.TestCase
):
    def test_preflight_accepts_exact_storage_target(self):
        fixture = Fixture()

        try:
            value = request()

            result = fixture.adapter().preflight(
                value,
                provider(),
            )

            self.assertTrue(
                result.compatible
            )

            self.assertEqual(
                result.checks[
                    "storageBinding"
                ][
                    "storage_target_id"
                ],
                "storage-local",
            )

        finally:
            fixture.close()

    def test_preflight_enforces_provider_capacity(self):
        fixture = Fixture()

        try:
            result = fixture.adapter().preflight(
                request(),
                provider(
                    estimated_disk_bytes=
                        800_000_000_000,
                ),
            )

            self.assertTrue(
                result.compatible
            )

            self.assertEqual(
                result.checks[
                    "storageCapacity"
                ][
                    "estimated_bytes"
                ],
                800_000_000_000,
            )

            self.assertEqual(
                result.checks[
                    "storageCapacity"
                ][
                    "reserve_bytes"
                ],
                160_000_000_000,
            )

            self.assertEqual(
                result.checks[
                    "storageCapacity"
                ][
                    "required_bytes"
                ],
                960_000_000_000,
            )

            self.assertEqual(
                fixture.verifier_calls[0][
                    "kwargs"
                ][
                    "minimum_free_bytes"
                ],
                960_000_000_000,
            )

        finally:
            fixture.close()

    def test_preflight_fails_missing_capacity_contract(self):
        fixture = Fixture()

        try:
            result = fixture.adapter().preflight(
                request(),
                {},
            )

            self.assertFalse(
                result.compatible
            )

            self.assertIn(
                "estimated disk capacity",
                " ".join(
                    result.errors
                ).lower(),
            )

            self.assertEqual(
                fixture.verifier_calls,
                [],
            )

        finally:
            fixture.close()

    def test_preflight_fails_nonpositive_capacity_contract(self):
        fixture = Fixture()

        try:
            result = fixture.adapter().preflight(
                request(),
                provider(
                    estimated_disk_bytes=0,
                ),
            )

            self.assertFalse(
                result.compatible
            )

            self.assertIn(
                "estimated disk capacity",
                " ".join(
                    result.errors
                ).lower(),
            )

            self.assertEqual(
                fixture.verifier_calls,
                [],
            )

        finally:
            fixture.close()

    def test_preflight_fails_missing_exact_target(self):
        fixture = Fixture()

        try:
            value = request(
                storage_target_id="missing"
            )

            result = fixture.adapter().preflight(
                value,
                provider(),
            )

            self.assertFalse(
                result.compatible
            )

            self.assertIn(
                "unavailable",
                " ".join(
                    result.errors
                ).lower(),
            )

        finally:
            fixture.close()

    def test_preflight_fails_unhealthy_storage(self):
        fixture = Fixture(
            storage_healthy=False
        )

        try:
            result = fixture.adapter().preflight(
                request(),
                provider(),
            )

            self.assertFalse(
                result.compatible
            )

            self.assertIn(
                "mount mismatch",
                result.errors,
            )

        finally:
            fixture.close()

    def test_execute_uses_guarded_command_and_secret_environment(self):
        fixture = Fixture()

        try:
            value = request()

            result = fixture.adapter().execute(
                value,
                {},
            )

            self.assertTrue(
                result.success
            )

            self.assertEqual(
                len(
                    fixture.runner_calls
                ),
                1,
            )

            call = (
                fixture.runner_calls[0]
            )

            self.assertEqual(
                call["command"][1:],
                [
                    "--execute",
                    "--confirm",
                    "INSTALL-seymour-bitcoin-node",
                ],
            )

            self.assertEqual(
                call["timeout"],
                900,
            )

            self.assertEqual(
                call["env"][
                    "BTC_RPC_PASSWORD"
                ],
                "x" * 32,
            )

            self.assertNotIn(
                "x" * 32,
                " ".join(
                    call["command"]
                ),
            )

            self.assertNotIn(
                "x" * 32,
                str(result.evidence),
            )

            self.assertEqual(
                len(fixture.prepared),
                1,
            )

            binding_file = (
                fixture.root
                / "bindings"
                / "seymour-bitcoin-node.env"
            )

            self.assertTrue(
                binding_file.is_file()
            )

        finally:
            fixture.close()

    def test_execute_stages_binding_before_runner(self):
        fixture = Fixture()

        try:
            result = fixture.adapter().execute(
                request(),
                provider(),
            )

            self.assertTrue(result.success)

            self.assertEqual(
                len(fixture.handoff_calls),
                1,
            )

            call = fixture.handoff_calls[0]

            self.assertEqual(
                call["data_directory"],
                fixture.root / "umbrel",
            )

            self.assertEqual(
                call["app_id"],
                "seymour-bitcoin-node",
            )

            self.assertEqual(
                call["binding_path"],
                fixture.root
                / "bindings"
                / "seymour-bitcoin-node.env",
            )

            self.assertTrue(
                call["binding_path"].is_file()
            )

            self.assertEqual(
                result.evidence[
                    "runtimeBindingHandoff"
                ]["staged"],
                True,
            )

            self.assertEqual(
                len(fixture.runner_calls),
                1,
            )

        finally:
            fixture.close()

    def test_execute_handoff_precedes_runner(self):
        fixture = Fixture()
        order = []

        original_handoff = fixture.handoff
        original_runner = fixture.runner

        def handoff(**kwargs):
            order.append("handoff")
            return original_handoff(**kwargs)

        def runner(command, env, timeout):
            order.append("runner")
            return original_runner(
                command,
                env,
                timeout,
            )

        try:
            adapter = fixture.adapter()
            adapter.binding_handoff = handoff
            adapter.command_runner = runner

            result = adapter.execute(
                request(),
                provider(),
            )

            self.assertTrue(result.success)
            self.assertEqual(
                order,
                ["handoff", "runner"],
            )

        finally:
            fixture.close()

    def test_relative_umbrel_data_directory_fails_closed(self):
        fixture = Fixture()

        try:
            with self.assertRaises(ValueError):
                UmbrelTargetInstallAdapter(
                    provider_controls=fixture.controls,
                    storage_resolver=fixture.resolver,
                    storage_verifier=fixture.verifier,
                    storage_preparer=fixture.preparer,
                    command_runner=fixture.runner,
                    state_reader=lambda app_id: {},
                    mount_inspector=lambda app_id: [],
                    script_available=lambda path: True,
                    runtime_host="umbrel-test",
                    binding_config_root=(
                        fixture.root / "bindings"
                    ),
                    umbrel_data_directory=Path(
                        "relative-umbrel"
                    ),
                    bch_local_data_path=(
                        fixture.root / "bch"
                    ),
                    binding_handoff=fixture.handoff,
                )

        finally:
            fixture.close()

    def test_failed_runner_fails_execution(self):
        fixture = Fixture(
            runner_code=7
        )

        try:
            result = fixture.adapter().execute(
                request(),
                {},
            )

            self.assertFalse(
                result.success
            )

            self.assertEqual(
                result.error,
                "install failed",
            )

        finally:
            fixture.close()

    def test_remote_bch_uses_hybrid_binding(self):
        fixture = Fixture(
            storage_target=target(
                target_id="storage-remote",
                target_type=(
                    StorageTargetType.REMOTE
                ),
                path="/mnt/seymour-bch",
            )
        )

        try:
            value = request(
                provider_id=(
                    "bitcoin-cash-mainnet"
                ),
                app_id="seymour-bch-node",
                storage_target_id=(
                    "storage-remote"
                ),
                rpc_port=8332,
                p2p_port=8333,
            )

            result = fixture.adapter().execute(
                value,
                {},
            )

            self.assertTrue(
                result.success
            )

            binding = (
                fixture.prepared[0]
            )

            self.assertEqual(
                binding.mode,
                RuntimeBindingMode.HYBRID_BLOCKS,
            )

            self.assertEqual(
                binding.blocks_path,
                Path(
                    "/mnt/seymour-bch"
                )
                / "bitcoin-cash-mainnet"
                / "blocks",
            )

            self.assertEqual(
                fixture.runner_calls[0][
                    "env"
                ][
                    "BCH_RPC_PASSWORD"
                ],
                "x" * 32,
            )

        finally:
            fixture.close()

    def test_verify_single_path_mount(self):
        fixture = Fixture()

        try:
            value = request()

            execution = (
                fixture.adapter().execute(
                    value,
                    {},
                )
            )

            binding = (
                fixture.prepared[0]
            )

            fixture.mounts = [{
                "Destination": "/data",
                "Source": str(
                    binding.data_path
                ),
            }]

            verification = (
                fixture.adapter().verify(
                    value,
                    {},
                    execution,
                )
            )

            self.assertTrue(
                verification.verified
            )

        finally:
            fixture.close()

    def test_verify_hybrid_bch_mounts(self):
        fixture = Fixture(
            storage_target=target(
                target_id="storage-remote",
                target_type=(
                    StorageTargetType.REMOTE
                ),
                path="/mnt/seymour-bch",
            )
        )

        try:
            value = request(
                provider_id=(
                    "bitcoin-cash-mainnet"
                ),
                app_id="seymour-bch-node",
                storage_target_id=(
                    "storage-remote"
                ),
                rpc_port=8332,
                p2p_port=8333,
            )

            adapter = fixture.adapter()

            execution = adapter.execute(
                value,
                {},
            )

            binding = (
                fixture.prepared[0]
            )

            fixture.mounts = [
                {
                    "Destination": "/data",
                    "Source": str(
                        binding.local_data_path
                    ),
                },
                {
                    "Destination":
                        "/data/blocks",
                    "Source": str(
                        binding.blocks_path
                    ),
                },
            ]

            verification = adapter.verify(
                value,
                {},
                execution,
            )

            self.assertTrue(
                verification.verified
            )

            self.assertTrue(
                verification.evidence[
                    "runtimeBlocksMountMatches"
                ]
            )

        finally:
            fixture.close()

    def test_verify_fails_wrong_data_mount(self):
        fixture = Fixture()

        try:
            value = request()

            adapter = fixture.adapter()

            execution = adapter.execute(
                value,
                {},
            )

            fixture.mounts = [{
                "Destination": "/data",
                "Source": "/wrong/path",
            }]

            verification = adapter.verify(
                value,
                {},
                execution,
            )

            self.assertFalse(
                verification.verified
            )

            self.assertIn(
                "/data mount",
                verification.error,
            )

        finally:
            fixture.close()

    def test_module_has_no_real_command_executor(self):
        from shared.blockchain_install import (
            umbrel_target,
        )

        source = Path(
            umbrel_target.__file__
        ).read_text()

        self.assertNotIn(
            "subprocess.run",
            source,
        )

        self.assertNotIn(
            "Popen(",
            source,
        )

        self.assertNotIn(
            "os.system",
            source,
        )

        self.assertNotIn(
            "paramiko",
            source.lower(),
        )


if __name__ == "__main__":
    unittest.main()
