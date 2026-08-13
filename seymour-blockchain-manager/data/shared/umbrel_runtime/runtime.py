from __future__ import annotations

import json
import os
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from .models import AppRuntimeState, ContainerState


class UmbrelRuntime:
    def __init__(
        self,
        *,
        data_directory: Path | None = None,
        app_store_root: Path | None = None,
        docker_binary: str = "docker",
    ) -> None:
        self.data_directory = (
            data_directory
            or Path(
                os.environ.get(
                    "UMBREL_DATA_DIRECTORY",
                    "/home/umbrel/umbrel",
                )
            )
        )

        self.app_store_root = (
            app_store_root
            or Path(
                os.environ.get(
                    "SEYMOUR_APP_STORE_ROOT",
                    "/home/umbrel/seymour-umbrel-app-store-git",
                )
            )
        )

        self.docker_binary = docker_binary

    @property
    def installed_apps_root(self) -> Path:
        return self.data_directory / "app-data"

    def source_app_path(self, app_id: str) -> Path:
        return self.app_store_root / app_id

    def installed_app_path(self, app_id: str) -> Path:
        return self.installed_apps_root / app_id

    def source_available(self, app_id: str) -> bool:
        return (
            self.source_app_path(app_id)
            / "umbrel-app.yml"
        ).is_file()

    def installed(self, app_id: str) -> bool:
        path = self.installed_app_path(app_id)
        return path.exists() and path.is_dir()

    def list_source_apps(self) -> list[str]:
        apps: list[str] = []

        if not self.app_store_root.is_dir():
            return apps

        for manifest in self.app_store_root.glob(
            "*/umbrel-app.yml"
        ):
            apps.append(
                manifest.parent.name
            )

        return sorted(apps)

    def list_installed_apps(self) -> list[str]:
        root = self.installed_apps_root

        if not root.is_dir():
            return []

        return sorted(
            item.name
            for item in root.iterdir()
            if item.is_dir()
        )

    def read_manifest(
        self,
        app_id: str,
    ) -> dict[str, Any]:
        manifest = (
            self.source_app_path(app_id)
            / "umbrel-app.yml"
        )

        if not manifest.exists():
            return {}

        result: dict[str, Any] = {}
        for raw_line in manifest.read_text().splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" not in line:
                continue

            key, value = line.split(":", 1)
            if key in {
                "id",
                "name",
                "version",
                "category",
                "port",
                "tagline",
            }:
                result[key] = value.strip().strip('"')

        return result

    def declared_dependencies(
        self,
        app_id: str,
    ) -> list[str]:
        manifest = (
            self.source_app_path(app_id)
            / "umbrel-app.yml"
        )

        if not manifest.exists():
            return []

        lines = manifest.read_text().splitlines()
        dependencies: list[str] = []
        in_dependencies = False

        for raw_line in lines:
            line = raw_line.rstrip()

            if line.startswith("dependencies:"):
                in_dependencies = True
                inline = line.split(":", 1)[1].strip()

                if inline == "[]":
                    return []

                continue

            if in_dependencies:
                stripped = line.strip()

                if not stripped:
                    continue

                if stripped.startswith("- "):
                    dependencies.append(
                        stripped[2:].strip()
                    )
                    continue

                if not line.startswith(" "):
                    break

        return dependencies

    def _docker(
        self,
        *args: str,
        timeout: int = 10,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                self.docker_binary,
                *args,
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )

    def docker_available(self) -> bool:
        try:
            result = self._docker(
                "version",
                "--format",
                "{{.Server.Version}}",
            )
            return result.returncode == 0
        except Exception:
            return False

    def containers_for_app(
        self,
        app_id: str,
    ) -> list[ContainerState]:
        if not self.docker_available():
            return []

        result = self._docker(
            "ps",
            "-a",
            "--filter",
            f"label=com.docker.compose.project={app_id}",
            "--format",
            "{{json .}}",
        )

        if result.returncode != 0:
            return []

        containers: list[ContainerState] = []

        for line in result.stdout.splitlines():
            if not line.strip():
                continue

            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue

            name = item.get("Names") or ""
            status_text = item.get("Status") or ""
            state = item.get("State") or ""

            inspect = self._docker(
                "inspect",
                name,
                "--format",
                "{{json .State}}",
            )

            health: bool | None = None
            started_at: str | None = None

            if inspect.returncode == 0:
                try:
                    state_payload = json.loads(
                        inspect.stdout.strip()
                    )
                    started_at = state_payload.get(
                        "StartedAt"
                    )
                    health_payload = state_payload.get(
                        "Health"
                    )

                    if isinstance(
                        health_payload,
                        dict,
                    ):
                        health = (
                            health_payload.get(
                                "Status"
                            )
                            == "healthy"
                        )
                except json.JSONDecodeError:
                    pass

            service = None
            labels = item.get("Labels") or ""

            for label in labels.split(","):
                if label.startswith(
                    "com.docker.compose.service="
                ):
                    service = label.split(
                        "=",
                        1,
                    )[1]

            containers.append(
                ContainerState(
                    name=name,
                    service=service,
                    status=status_text,
                    running=state == "running",
                    healthy=health,
                    image=item.get("Image"),
                    started_at=started_at,
                )
            )

        return containers

    def lifecycle_status(
        self,
        *,
        installed: bool,
        containers: list[ContainerState],
    ) -> str:
        if not installed:
            return "not-installed"

        if not containers:
            return "installed-stopped"

        if all(
            container.running
            for container in containers
        ):
            health_values = [
                container.healthy
                for container in containers
                if container.healthy is not None
            ]

            if (
                health_values
                and not all(health_values)
            ):
                return "running-unhealthy"

            return "running"

        if any(
            container.running
            for container in containers
        ):
            return "partially-running"

        return "stopped"

    def probe_health(
        self,
        *,
        host: str,
        port: int,
        path: str = "/api/health",
    ) -> dict[str, Any]:
        url = f"http://{host}:{port}{path}"

        try:
            with urllib.request.urlopen(
                url,
                timeout=5,
            ) as response:
                body = response.read().decode()
                payload = json.loads(body)

            return {
                "reachable": True,
                "statusCode": response.status,
                "payload": payload,
                "url": url,
            }

        except urllib.error.HTTPError as exc:
            body = exc.read().decode(
                errors="replace"
            )

            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                payload = {"raw": body}

            return {
                "reachable": True,
                "statusCode": exc.code,
                "payload": payload,
                "url": url,
            }

        except Exception as exc:
            return {
                "reachable": False,
                "error": str(exc),
                "url": url,
            }

    def collect_logs(
        self,
        app_id: str,
        *,
        tail: int = 100,
    ) -> dict[str, Any]:
        logs: dict[str, Any] = {}

        for container in self.containers_for_app(
            app_id
        ):
            result = self._docker(
                "logs",
                "--tail",
                str(tail),
                container.name,
                timeout=20,
            )

            logs[container.name] = {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0,
            }

        return logs

    def inspect_app(
        self,
        app_id: str,
        *,
        health_host: str | None = None,
        health_port: int | None = None,
    ) -> AppRuntimeState:
        errors: list[str] = []
        source_available = self.source_available(
            app_id
        )
        installed = self.installed(
            app_id
        )
        manifest = self.read_manifest(
            app_id
        )
        dependencies = self.declared_dependencies(
            app_id
        )
        missing_dependencies = [
            dependency
            for dependency in dependencies
            if not self.installed(dependency)
        ]

        try:
            containers = self.containers_for_app(
                app_id
            )
        except Exception as exc:
            containers = []
            errors.append(str(exc))

        health: dict[str, Any] = {}

        if (
            health_host is not None
            and health_port is not None
        ):
            health = self.probe_health(
                host=health_host,
                port=health_port,
            )

        return AppRuntimeState(
            app_id=app_id,
            installed=installed,
            source_available=source_available,
            version=manifest.get("version"),
            lifecycle_status=self.lifecycle_status(
                installed=installed,
                containers=containers,
            ),
            containers=containers,
            dependencies=dependencies,
            missing_dependencies=(
                missing_dependencies
            ),
            health=health,
            paths={
                "source": str(
                    self.source_app_path(app_id)
                ),
                "installed": str(
                    self.installed_app_path(app_id)
                ),
            },
            errors=errors,
        )
