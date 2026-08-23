from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class RuntimeBindingMode(StrEnum):
    SINGLE_PATH = "single-path"
    HYBRID_BLOCKS = "hybrid-blocks"


@dataclass(frozen=True)
class RuntimeBinding:
    provider_id: str
    app_id: str
    mode: RuntimeBindingMode
    data_path: Path | None = None
    local_data_path: Path | None = None
    blocks_path: Path | None = None

    def validate(self) -> None:
        if not self.provider_id:
            raise ValueError("provider_id is required")

        if not self.app_id:
            raise ValueError("app_id is required")

        if self.mode == RuntimeBindingMode.SINGLE_PATH:
            if self.data_path is None:
                raise ValueError(
                    "single-path binding requires data_path"
                )

            _require_absolute(self.data_path)

            if (
                self.local_data_path is not None
                or self.blocks_path is not None
            ):
                raise ValueError(
                    "single-path binding cannot contain "
                    "hybrid paths"
                )

        elif self.mode == RuntimeBindingMode.HYBRID_BLOCKS:
            if self.local_data_path is None:
                raise ValueError(
                    "hybrid-blocks binding requires "
                    "local_data_path"
                )

            if self.blocks_path is None:
                raise ValueError(
                    "hybrid-blocks binding requires "
                    "blocks_path"
                )

            _require_absolute(self.local_data_path)
            _require_absolute(self.blocks_path)

            if self.data_path is not None:
                raise ValueError(
                    "hybrid-blocks binding cannot contain "
                    "data_path"
                )

        else:
            raise ValueError(
                f"unsupported runtime binding mode: {self.mode}"
            )

    def environment(self) -> dict[str, str]:
        self.validate()

        values = {
            "SEYMOUR_BLOCKCHAIN_PROVIDER_ID":
                self.provider_id,
            "SEYMOUR_BLOCKCHAIN_APP_ID":
                self.app_id,
        }

        if self.mode == RuntimeBindingMode.SINGLE_PATH:
            assert self.data_path is not None
            values["SEYMOUR_BLOCKCHAIN_DATA_PATH"] = str(
                self.data_path
            )

        else:
            assert self.local_data_path is not None
            assert self.blocks_path is not None

            values[
                "SEYMOUR_BLOCKCHAIN_LOCAL_DATA_PATH"
            ] = str(self.local_data_path)

            values[
                "SEYMOUR_BLOCKCHAIN_BLOCKS_PATH"
            ] = str(self.blocks_path)

        return values


def _require_absolute(path: Path) -> None:
    value = str(path)

    if (
        not path.is_absolute()
        or "\n" in value
        or "\r" in value
    ):
        raise ValueError(
            f"runtime binding path must be absolute: {value!r}"
        )


def serialize_runtime_binding(
    binding: RuntimeBinding,
) -> str:
    values = binding.environment()

    order = [
        "SEYMOUR_BLOCKCHAIN_PROVIDER_ID",
        "SEYMOUR_BLOCKCHAIN_APP_ID",
        "SEYMOUR_BLOCKCHAIN_DATA_PATH",
        "SEYMOUR_BLOCKCHAIN_LOCAL_DATA_PATH",
        "SEYMOUR_BLOCKCHAIN_BLOCKS_PATH",
    ]

    lines = [
        f"{key}={values[key]}"
        for key in order
        if key in values
    ]

    return "\n".join(lines) + "\n"
