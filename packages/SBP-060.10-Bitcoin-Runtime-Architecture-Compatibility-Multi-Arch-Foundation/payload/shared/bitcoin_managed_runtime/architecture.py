from __future__ import annotations

import json
import platform
import subprocess
from dataclasses import dataclass
from typing import Any


def normalize_architecture(value: str | None) -> str | None:
    raw = str(value or "").strip().lower()
    if raw in {"x86_64", "amd64"}:
        return "amd64"
    if raw in {"aarch64", "arm64", "arm64/v8"}:
        return "arm64"
    return raw or None


@dataclass(frozen=True)
class ImageArchitectureReport:
    image: str
    host_architecture: str | None
    image_architecture: str | None
    compatible: bool
    inspect_available: bool
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "image": self.image,
            "hostArchitecture": self.host_architecture,
            "imageArchitecture": self.image_architecture,
            "compatible": self.compatible,
            "inspectAvailable": self.inspect_available,
            "error": self.error,
        }


def host_architecture() -> str | None:
    return normalize_architecture(platform.machine())


def inspect_local_image_architecture(image: str) -> tuple[str | None, str | None]:
    commands = [
        [
            "docker",
            "image",
            "inspect",
            image,
            "--format",
            "{{json .Architecture}}",
        ],
        [
            "sudo",
            "-n",
            "docker",
            "image",
            "inspect",
            image,
            "--format",
            "{{json .Architecture}}",
        ],
    ]

    result = None
    errors = []

    for command in commands:
        try:
            candidate = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
        except Exception as exc:
            errors.append(str(exc))
            continue

        if candidate.returncode == 0:
            result = candidate
            break

        errors.append(
            candidate.stderr.strip()
            or candidate.stdout.strip()
            or "docker image inspect failed"
        )

    if result is None:
        return None, " | ".join(errors)

    raw = result.stdout.strip()
    try:
        raw = json.loads(raw)
    except Exception:
        raw = raw.strip('"')

    return normalize_architecture(str(raw)), None


def architecture_report(image: str) -> ImageArchitectureReport:
    host = host_architecture()
    image_arch, error = inspect_local_image_architecture(image)
    available = image_arch is not None

    return ImageArchitectureReport(
        image=image,
        host_architecture=host,
        image_architecture=image_arch,
        compatible=bool(host and image_arch and host == image_arch),
        inspect_available=available,
        error=error,
    )
