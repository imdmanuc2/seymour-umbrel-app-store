from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any, Callable, Mapping

from .binding import (
    StorageBindingPlan,
    build_binding_plan,
)
from .models import (
    StorageTarget,
    StorageTargetType,
)
from .preflight import capacity_policy
from .request import InstallRequest
from .runtime_binding import (
    RuntimeBinding,
    RuntimeBindingMode,
    serialize_runtime_binding,
)
from .runtime_binding_handoff import (
    stage_runtime_binding,
)
from .target import (
    TargetInstallExecution,
    TargetInstallPreflight,
    TargetInstallVerification,
)


@dataclass(frozen=True)
class UmbrelProviderControl:
    """
    Target-local executable details for one provider.

    Application identity remains owned by the canonical provider
    catalog. This mapping owns only target executable details.
    """

    install_script: Path
    rpc_prefix: str


@dataclass(frozen=True)
class UmbrelCommandResult:
    """
    Sanitized result returned by the injected target command runner.

    Environment variables are intentionally not retained here.
    """

    return_code: int
    stdout: str = ""
    stderr: str = ""

    @property
    def succeeded(self) -> bool:
        return self.return_code == 0


class UmbrelTargetInstallAdapter:
    """
    Umbrel-specific blockchain installation adapter.

    All mutation/inspection boundaries are injected. This module
    intentionally provides no subprocess, Docker, SSH, or Nexus
    execution implementation.
    """

    adapter_type = "umbrel"

    def __init__(
        self,
        *,
        provider_controls: Mapping[
            str,
            UmbrelProviderControl,
        ],
        storage_resolver: Callable[
            [str],
            StorageTarget | None,
        ],
        storage_verifier: Callable[..., dict[str, Any]],
        storage_preparer: Callable[
            [RuntimeBinding],
            Any,
        ],
        command_runner: Callable[
            [list[str], dict[str, str], int],
            UmbrelCommandResult,
        ],
        state_reader: Callable[
            [str],
            dict[str, Any],
        ],
        mount_inspector: Callable[
            [str],
            list[dict[str, Any]],
        ],
        script_available: Callable[
            [Path],
            bool,
        ],
        runtime_host: str,
        binding_config_root: Path,
        umbrel_data_directory: Path,
        bch_local_data_path: Path,
        binding_handoff: Callable[
            ...,
            dict[str, object],
        ] = stage_runtime_binding,
        environment_provider: Callable[
            [],
            Mapping[str, str],
        ] = os.environ.copy,
    ) -> None:
        self.provider_controls = dict(
            provider_controls
        )
        self.storage_resolver = (
            storage_resolver
        )
        self.storage_verifier = (
            storage_verifier
        )
        self.storage_preparer = (
            storage_preparer
        )
        self.command_runner = (
            command_runner
        )
        self.state_reader = state_reader
        self.mount_inspector = (
            mount_inspector
        )
        self.script_available = (
            script_available
        )
        self.runtime_host = (
            str(runtime_host).strip()
        )
        self.binding_config_root = Path(
            binding_config_root
        )
        self.umbrel_data_directory = Path(
            umbrel_data_directory
        )
        self.bch_local_data_path = Path(
            bch_local_data_path
        )
        self.binding_handoff = binding_handoff
        self.environment_provider = (
            environment_provider
        )

        if not self.runtime_host:
            raise ValueError(
                "runtime_host is required"
            )

        if not self.umbrel_data_directory.is_absolute():
            raise ValueError(
                "umbrel_data_directory must be absolute"
            )

    def _control(
        self,
        provider_id: str,
    ) -> UmbrelProviderControl:
        control = self.provider_controls.get(
            provider_id
        )

        if control is None:
            raise ValueError(
                "Provider installation control "
                "is not configured for this target."
            )

        return control

    def _storage_target(
        self,
        storage_target_id: str,
    ) -> StorageTarget:
        target = self.storage_resolver(
            storage_target_id
        )

        if target is None:
            raise ValueError(
                "Selected storage target is unavailable."
            )

        if (
            target.target_id
            != storage_target_id
        ):
            raise ValueError(
                "Storage resolver returned a different "
                "target than requested."
            )

        return target

    def _binding_plan(
        self,
        request: InstallRequest,
        target: StorageTarget,
    ) -> StorageBindingPlan:
        return build_binding_plan(
            provider_id=request.provider_id,
            runtime_host=self.runtime_host,
            storage_target=target,
            target_is_data_root=(
                target.target_type
                == StorageTargetType.REMOTE
            ),
        )

    def _runtime_binding(
        self,
        request: InstallRequest,
        target: StorageTarget,
        plan: StorageBindingPlan,
    ) -> RuntimeBinding:
        data_path = Path(
            plan.data_path
        )

        hybrid_bch = (
            request.provider_id
            == "bitcoin-cash-mainnet"
            and target.target_type
            == StorageTargetType.REMOTE
        )

        if hybrid_bch:
            binding = RuntimeBinding(
                provider_id=request.provider_id,
                app_id=request.app_id,
                mode=(
                    RuntimeBindingMode.HYBRID_BLOCKS
                ),
                local_data_path=(
                    self.bch_local_data_path
                ),
                blocks_path=(
                    data_path / "blocks"
                ),
            )

        else:
            binding = RuntimeBinding(
                provider_id=request.provider_id,
                app_id=request.app_id,
                mode=(
                    RuntimeBindingMode.SINGLE_PATH
                ),
                data_path=data_path,
            )

        binding.validate()
        return binding

    def _prepare(
        self,
        request: InstallRequest,
    ) -> tuple[
        UmbrelProviderControl,
        StorageTarget,
        StorageBindingPlan,
        RuntimeBinding,
    ]:
        control = self._control(
            request.provider_id
        )

        target = self._storage_target(
            request.storage_target_id
        )

        plan = self._binding_plan(
            request,
            target,
        )

        binding = self._runtime_binding(
            request,
            target,
            plan,
        )

        return (
            control,
            target,
            plan,
            binding,
        )

    def preflight(
        self,
        request: InstallRequest,
        provider: dict[str, Any],
    ) -> TargetInstallPreflight:
        errors: list[str] = []
        checks: dict[str, Any] = {}

        try:
            estimated_disk_bytes = int(
                provider.get(
                    "estimatedDiskBytes",
                    0,
                )
            )

            if estimated_disk_bytes <= 0:
                raise ValueError(
                    "Provider estimated disk capacity "
                    "is missing or invalid."
                )

            capacity = capacity_policy(
                estimated_disk_bytes
            )

            checks["storageCapacity"] = (
                capacity.to_dict()
            )

            (
                control,
                target,
                plan,
                binding,
            ) = self._prepare(request)

        except Exception as exc:
            return TargetInstallPreflight(
                compatible=False,
                checks={},
                errors=(str(exc),),
            )

        script_ok = bool(
            self.script_available(
                control.install_script
            )
        )

        checks["installScript"] = {
            "path": str(
                control.install_script
            ),
            "available": script_ok,
        }

        if not script_ok:
            errors.append(
                "Provider installation control "
                "is unavailable on the target."
            )

        checks["storageBinding"] = (
            plan.to_dict()
        )

        if not plan.eligible:
            errors.extend(
                str(item)
                for item in plan.errors
            )

        guard_data_path = (
            binding.blocks_path
            if (
                binding.mode
                == RuntimeBindingMode.HYBRID_BLOCKS
            )
            else binding.data_path
        )

        storage_guard = (
            self.storage_verifier(
                target,
                minimum_free_bytes=(
                    capacity.required_bytes
                ),
                data_path=guard_data_path,
            )
        )

        checks["storageMountGuard"] = (
            storage_guard
        )

        if not bool(
            storage_guard.get("healthy")
        ):
            guard_errors = (
                storage_guard.get("errors")
                or []
            )

            if guard_errors:
                errors.extend(
                    str(item)
                    for item in guard_errors
                )
            else:
                errors.append(
                    "Selected storage target failed "
                    "target verification."
                )

        checks["runtimeBinding"] = {
            "providerId":
                binding.provider_id,
            "appId":
                binding.app_id,
            "mode":
                binding.mode.value,
            "dataPath": (
                str(binding.data_path)
                if binding.data_path
                is not None
                else None
            ),
            "localDataPath": (
                str(
                    binding.local_data_path
                )
                if binding.local_data_path
                is not None
                else None
            ),
            "blocksPath": (
                str(binding.blocks_path)
                if binding.blocks_path
                is not None
                else None
            ),
        }

        return TargetInstallPreflight(
            compatible=not errors,
            checks=checks,
            errors=tuple(errors),
        )

    def _write_binding(
        self,
        binding: RuntimeBinding,
    ) -> dict[str, Any]:
        binding.validate()

        self.binding_config_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        path = (
            self.binding_config_root
            / f"{binding.app_id}.env"
        )

        temporary = path.with_suffix(
            ".env.tmp"
        )

        temporary.write_text(
            serialize_runtime_binding(
                binding
            )
        )
        temporary.chmod(0o600)
        temporary.replace(path)

        return {
            "path": str(path),
            "providerId":
                binding.provider_id,
            "appId":
                binding.app_id,
            "mode":
                binding.mode.value,
        }

    def _environment(
        self,
        *,
        request: InstallRequest,
        control: UmbrelProviderControl,
        binding: RuntimeBinding,
    ) -> dict[str, str]:
        env = dict(
            self.environment_provider()
        )

        for key in (
            "SEYMOUR_BLOCKCHAIN_DATA_PATH",
            "SEYMOUR_BLOCKCHAIN_LOCAL_DATA_PATH",
            "SEYMOUR_BLOCKCHAIN_BLOCKS_PATH",
        ):
            env.pop(key, None)

        prefix = (
            control.rpc_prefix
            .strip()
            .upper()
        )

        if not prefix:
            raise ValueError(
                "Provider RPC environment prefix "
                "is missing."
            )

        env.update({
            f"{prefix}_RPC_USER":
                request.rpc_user,
            f"{prefix}_RPC_PASSWORD":
                request.rpc_password,
            f"{prefix}_RPC_PORT":
                str(request.rpc_port),
            f"{prefix}_P2P_PORT":
                str(request.p2p_port),
            "SEYMOUR_NODE_NAME":
                request.node_name,
        })

        env.update(
            binding.environment()
        )

        return env

    def execute(
        self,
        request: InstallRequest,
        provider: dict[str, Any],
    ) -> TargetInstallExecution:
        del provider

        try:
            (
                control,
                _target,
                plan,
                binding,
            ) = self._prepare(request)

            if not plan.eligible:
                return TargetInstallExecution(
                    success=False,
                    error=(
                        "Selected storage target is "
                        "not eligible for runtime binding."
                    ),
                )

            if not self.script_available(
                control.install_script
            ):
                return TargetInstallExecution(
                    success=False,
                    error=(
                        "Provider installation control "
                        "is unavailable on the target."
                    ),
                )

            preparation = (
                self.storage_preparer(
                    binding
                )
            )

            binding_config = (
                self._write_binding(
                    binding
                )
            )

            binding_handoff = (
                self.binding_handoff(
                    binding_path=Path(
                        binding_config["path"]
                    ),
                    data_directory=(
                        self.umbrel_data_directory
                    ),
                    app_id=binding.app_id,
                )
            )

            env = self._environment(
                request=request,
                control=control,
                binding=binding,
            )

            command = [
                str(
                    control.install_script
                ),
                "--execute",
                "--confirm",
                request.confirmation,
                "--data-directory",
                str(
                    self.umbrel_data_directory
                ),
            ]

            completed = (
                self.command_runner(
                    command,
                    env,
                    900,
                )
            )

            if not completed.succeeded:
                return TargetInstallExecution(
                    success=False,
                    evidence={
                        "storageBinding":
                            plan.to_dict(),
                        "runtimeBindingConfig":
                            binding_config,
                        "runtimeBindingHandoff":
                            binding_handoff,
                        "storagePreparation":
                            preparation,
                        "command": command,
                        "returnCode":
                            completed.return_code,
                    },
                    error=(
                        completed.stderr
                        or completed.stdout
                        or (
                            "Target installation "
                            "command failed."
                        )
                    ),
                )

            try:
                result = (
                    json.loads(
                        completed.stdout
                    )
                    if completed.stdout
                    else None
                )
            except json.JSONDecodeError as exc:
                return TargetInstallExecution(
                    success=False,
                    evidence={
                        "storageBinding":
                            plan.to_dict(),
                        "runtimeBindingConfig":
                            binding_config,
                        "runtimeBindingHandoff":
                            binding_handoff,
                        "storagePreparation":
                            preparation,
                        "command": command,
                        "returnCode":
                            completed.return_code,
                    },
                    error=(
                        "Target installation returned "
                        f"invalid JSON: {exc}"
                    ),
                )

            return TargetInstallExecution(
                success=True,
                result=result,
                evidence={
                    "storageBinding":
                        plan.to_dict(),
                    "runtimeBindingConfig":
                        binding_config,
                    "runtimeBindingHandoff":
                        binding_handoff,
                    "storagePreparation":
                        preparation,
                    "command": command,
                    "returnCode":
                        completed.return_code,
                },
            )

        except Exception as exc:
            return TargetInstallExecution(
                success=False,
                error=str(exc),
            )

    def verify(
        self,
        request: InstallRequest,
        provider: dict[str, Any],
        execution: TargetInstallExecution,
    ) -> TargetInstallVerification:
        del provider

        if not execution.success:
            return TargetInstallVerification(
                verified=False,
                error=(
                    execution.error
                    or "Installation did not succeed."
                ),
            )

        try:
            (
                _control,
                target,
                plan,
                binding,
            ) = self._prepare(request)

            state = self.state_reader(
                request.app_id
            )

            state_verified = bool(
                state.get("success")
            )

            mounts = self.mount_inspector(
                request.app_id
            )

            data_mount_source = None
            blocks_mount_source = None

            for item in mounts:
                destination = item.get(
                    "Destination"
                )

                if destination == "/data":
                    data_mount_source = (
                        item.get("Source")
                    )

                elif (
                    destination
                    == "/data/blocks"
                ):
                    blocks_mount_source = (
                        item.get("Source")
                    )

            requested_data_path = (
                binding.local_data_path
                if (
                    binding.mode
                    == RuntimeBindingMode.HYBRID_BLOCKS
                )
                else binding.data_path
            )

            assert (
                requested_data_path
                is not None
            )

            requested_source = str(
                requested_data_path.resolve()
            )

            mount_matches = (
                data_mount_source
                is not None
                and str(
                    Path(
                        data_mount_source
                    ).resolve()
                )
                == requested_source
            )

            requested_blocks_source = (
                str(
                    binding.blocks_path.resolve()
                )
                if binding.blocks_path
                is not None
                else None
            )

            blocks_mount_matches = (
                True
                if requested_blocks_source
                is None
                else (
                    blocks_mount_source
                    is not None
                    and str(
                        Path(
                            blocks_mount_source
                        ).resolve()
                    )
                    == requested_blocks_source
                )
            )

            verified = (
                state_verified
                and mount_matches
                and blocks_mount_matches
            )

            error = None

            if not state_verified:
                error = (
                    "Umbrel native application "
                    "state verification failed."
                )

            elif not mount_matches:
                error = (
                    "Runtime /data mount does not "
                    "match the requested runtime "
                    "storage path."
                )

            elif not blocks_mount_matches:
                error = (
                    "Runtime /data/blocks mount does "
                    "not match the selected advanced "
                    "storage target."
                )

            return TargetInstallVerification(
                verified=verified,
                evidence={
                    "state": state,
                    "storageBinding":
                        plan.to_dict(),
                    "storageTargetId":
                        target.target_id,
                    "bindingMode":
                        binding.mode.value,
                    "requestedDataPath":
                        requested_source,
                    "runtimeDataMountSource":
                        data_mount_source,
                    "runtimeDataMountMatches":
                        mount_matches,
                    "requestedBlocksPath":
                        requested_blocks_source,
                    "runtimeBlocksMountSource":
                        blocks_mount_source,
                    "runtimeBlocksMountMatches":
                        blocks_mount_matches,
                },
                error=error,
            )

        except Exception as exc:
            return TargetInstallVerification(
                verified=False,
                error=str(exc),
            )
