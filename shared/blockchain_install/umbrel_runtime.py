from __future__ import annotations

import socket
from pathlib import Path
from typing import Mapping

from shared.umbrel_control import (
    UmbrelAppControlBridge,
)

from .runtime_binding_handoff import (
    stage_runtime_binding,
)
from .storage import (
    verify_storage_target,
)
from .storage_inventory import (
    storage_target_by_id,
)
from .storage_preparer import (
    prepare_runtime_storage,
)
from .umbrel_execution import (
    discover_node_container,
    inspect_container_mounts,
    run_guarded_command,
    script_available,
)
from .umbrel_target import (
    UmbrelProviderControl,
    UmbrelTargetInstallAdapter,
)


def canonical_provider_controls(
    repository: Path,
) -> Mapping[str, UmbrelProviderControl]:
    """
    Resolve provider controls from the canonical Seymour repository.

    No standalone Blockchain Manager path is used here.
    """
    root = Path(repository)

    return {
        "bitcoin-mainnet": UmbrelProviderControl(
            install_script=(
                root
                / "scripts"
                / "seymour-install-btc"
            ),
            rpc_prefix="BTC",
        ),
        "bitcoin-cash-mainnet": UmbrelProviderControl(
            install_script=(
                root
                / "scripts"
                / "seymour-install-bch"
            ),
            rpc_prefix="BCH",
        ),
        "monero-mainnet": UmbrelProviderControl(
            install_script=(
                root
                / "scripts"
                / "seymour-install-monero"
            ),
            rpc_prefix="XMR",
        ),
    }


def neutral_binding_config_root(
    umbrel_data_directory: Path,
) -> Path:
    """
    Shared target-local working location for runtime bindings.
    """
    root = Path(
        umbrel_data_directory
    )

    if not root.is_absolute():
        raise ValueError(
            "Umbrel data directory must be absolute."
        )

    return (
        root
        / "seymour-evidence"
        / "blockchain-install"
        / "runtime-bindings"
    )


def neutral_control_evidence_root(
    umbrel_data_directory: Path,
) -> Path:
    """
    Shared evidence location for Umbrel lifecycle operations.
    """
    root = Path(
        umbrel_data_directory
    )

    if not root.is_absolute():
        raise ValueError(
            "Umbrel data directory must be absolute."
        )

    return (
        root
        / "seymour-evidence"
        / "blockchain-install"
        / "app-control"
    )


def default_bch_local_data_path(
    umbrel_data_directory: Path,
) -> Path:
    """
    BCH local chainstate path used when remote storage receives blocks.

    This is derived from the supplied Umbrel data directory and is
    therefore not tied to a fixed host root.
    """
    root = Path(
        umbrel_data_directory
    )

    if not root.is_absolute():
        raise ValueError(
            "Umbrel data directory must be absolute."
        )

    return (
        root
        / "app-data"
        / "seymour-bch-node"
        / "data"
        / "node"
    )


def build_umbrel_target_install_adapter(
    *,
    repository: Path,
    umbrel_data_directory: Path,
    remote_targets_path: Path | None = None,
    binding_config_root: Path | None = None,
    bch_local_data_path: Path | None = None,
    runtime_host: str | None = None,
    endpoint: str = "ws://localhost/trpc",
    docker_socket: Path | None = None,
) -> UmbrelTargetInstallAdapter:
    """
    Construct the production Umbrel target adapter exclusively from
    shared Seymour primitives.

    Construction performs no install, lifecycle mutation, storage
    preparation, provider execution, or credential generation.
    """
    repo = Path(repository)
    data_root = Path(
        umbrel_data_directory
    )

    if not repo.is_absolute():
        raise ValueError(
            "Repository path must be absolute."
        )

    if not data_root.is_absolute():
        raise ValueError(
            "Umbrel data directory must be absolute."
        )

    binding_root = (
        Path(binding_config_root)
        if binding_config_root is not None
        else neutral_binding_config_root(
            data_root
        )
    )

    if not binding_root.is_absolute():
        raise ValueError(
            "Binding config root must be absolute."
        )

    bch_path = (
        Path(bch_local_data_path)
        if bch_local_data_path is not None
        else default_bch_local_data_path(
            data_root
        )
    )

    if not bch_path.is_absolute():
        raise ValueError(
            "BCH local data path must be absolute."
        )

    host = str(
        runtime_host
        if runtime_host is not None
        else socket.gethostname()
    ).strip()

    if not host:
        raise ValueError(
            "Runtime host is required."
        )

    helper_path = (
        repo
        / "shared"
        / "umbrel_control"
        / "native-client.ts"
    )

    bridge = UmbrelAppControlBridge(
        helper_path=helper_path,
        data_directory=data_root,
        endpoint=str(endpoint),
        evidence_directory=(
            neutral_control_evidence_root(
                data_root
            )
        ),
        runtime_binding_directory=(
            binding_root
        ),
    )

    def resolve_storage(
        target_id: str,
    ):
        return storage_target_by_id(
            target_id,
            local_path=data_root,
            remote_targets_path=(
                Path(remote_targets_path)
                if remote_targets_path is not None
                else None
            ),
        )

    def read_state(
        app_id: str,
    ) -> dict:
        operation = bridge.execute(
            "state",
            app_id,
        )
        return operation.to_dict()

    def inspect_mounts(
        app_id: str,
    ) -> list[dict]:
        socket_value = (
            Path(docker_socket)
            if docker_socket is not None
            else None
        )

        container_name = (
            discover_node_container(
                app_id,
                socket_path=socket_value,
            )
        )

        if not container_name:
            raise RuntimeError(
                "Umbrel node container was not found "
                f"for {app_id}."
            )

        return inspect_container_mounts(
            container_name,
            socket_path=socket_value,
        )

    return UmbrelTargetInstallAdapter(
        provider_controls=(
            canonical_provider_controls(
                repo
            )
        ),
        storage_resolver=resolve_storage,
        storage_verifier=(
            verify_storage_target
        ),
        storage_preparer=(
            prepare_runtime_storage
        ),
        command_runner=(
            run_guarded_command
        ),
        state_reader=read_state,
        mount_inspector=inspect_mounts,
        script_available=(
            script_available
        ),
        runtime_host=host,
        binding_config_root=(
            binding_root
        ),
        umbrel_data_directory=(
            data_root
        ),
        bch_local_data_path=(
            bch_path
        ),
        binding_handoff=(
            stage_runtime_binding
        ),
    )
