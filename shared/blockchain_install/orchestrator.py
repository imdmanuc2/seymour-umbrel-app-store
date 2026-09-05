from __future__ import annotations

from typing import Any
from uuid import uuid4

from .execution import InstallResult
from .request import InstallRequest
from .target import TargetInstallAdapter
from .validation import (
    provider_from_catalog,
    validate_install_request,
)


class SharedInstallOrchestrator:
    """
    Provider-neutral blockchain installation orchestration.

    Target-specific execution remains owned by TargetInstallAdapter.
    """

    def __init__(
        self,
        *,
        catalog_path,
        target_adapter: TargetInstallAdapter,
    ) -> None:
        self.catalog_path = catalog_path
        self.target_adapter = target_adapter

    def execute(
        self,
        request: InstallRequest,
    ) -> InstallResult:
        operation_id = str(uuid4())

        try:
            validate_install_request(
                request,
                self.catalog_path,
            )

            provider = provider_from_catalog(
                self.catalog_path,
                request.provider_id,
            )

            preflight = self.target_adapter.preflight(
                request,
                provider,
            )

            if not preflight.compatible:
                return InstallResult(
                    operation_id=operation_id,
                    status="failed",
                    result={
                        "preflight":
                            preflight.to_dict(),
                    },
                    verification=None,
                    error="Installation preflight failed.",
                )

            execution = self.target_adapter.execute(
                request,
                provider,
            )

            if not execution.success:
                return InstallResult(
                    operation_id=operation_id,
                    status="failed",
                    result={
                        "preflight":
                            preflight.to_dict(),
                        "execution":
                            execution.to_dict(),
                    },
                    verification=None,
                    error=(
                        execution.error
                        or "Target installation failed."
                    ),
                )

            verification = (
                self.target_adapter.verify(
                    request,
                    provider,
                    execution,
                )
            )

            return InstallResult(
                operation_id=operation_id,
                status=(
                    "succeeded"
                    if verification.verified
                    else "failed"
                ),
                result={
                    "preflight":
                        preflight.to_dict(),
                    "execution":
                        execution.to_dict(),
                },
                verification=(
                    verification.to_dict()
                ),
                error=(
                    None
                    if verification.verified
                    else (
                        verification.error
                        or "Installation verification failed."
                    )
                ),
            )

        except Exception as exc:
            return InstallResult(
                operation_id=operation_id,
                status="failed",
                result=None,
                verification=None,
                error=str(exc),
            )
