from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


class CatalogValidationError(ValueError):
    pass


@dataclass(frozen=True)
class ProviderRecord:
    provider_id: str
    display_name: str
    ticker: str
    family: str
    implementation: str
    node_version: str
    network: str
    mining_algorithm: str
    supported_architectures: tuple[str, ...]
    default_ports: dict[str, int]
    estimated_disk_bytes: int
    availability: str
    selectable: bool
    production_image: str | None

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "ProviderRecord":
        required = {
            "providerId",
            "displayName",
            "ticker",
            "family",
            "implementation",
            "nodeVersion",
            "network",
            "miningAlgorithm",
            "supportedArchitectures",
            "defaultPorts",
            "estimatedDiskBytes",
            "availability",
            "selectable",
            "productionImage",
        }
        missing = required - data.keys()

        if missing:
            raise CatalogValidationError(
                "Provider is missing fields: "
                + ", ".join(sorted(missing))
            )

        record = cls(
            provider_id=str(data["providerId"]),
            display_name=str(data["displayName"]),
            ticker=str(data["ticker"]),
            family=str(data["family"]),
            implementation=str(data["implementation"]),
            node_version=str(data["nodeVersion"]),
            network=str(data["network"]),
            mining_algorithm=str(
                data["miningAlgorithm"]
            ),
            supported_architectures=tuple(
                str(value)
                for value in data[
                    "supportedArchitectures"
                ]
            ),
            default_ports={
                str(key): int(value)
                for key, value in data[
                    "defaultPorts"
                ].items()
            },
            estimated_disk_bytes=int(
                data["estimatedDiskBytes"]
            ),
            availability=str(data["availability"]),
            selectable=bool(data["selectable"]),
            production_image=(
                str(data["productionImage"])
                if data["productionImage"]
                else None
            ),
        )
        record.validate()
        return record

    def validate(self) -> None:
        allowed = {"live", "planned", "disabled"}

        if self.availability not in allowed:
            raise CatalogValidationError(
                f"Invalid availability for "
                f"{self.provider_id}: "
                f"{self.availability}"
            )

        if not self.supported_architectures:
            raise CatalogValidationError(
                f"{self.provider_id} has no architectures"
            )

        if not self.default_ports:
            raise CatalogValidationError(
                f"{self.provider_id} has no ports"
            )

        if self.estimated_disk_bytes <= 0:
            raise CatalogValidationError(
                f"{self.provider_id} has invalid disk estimate"
            )

        if self.selectable:
            if self.availability != "live":
                raise CatalogValidationError(
                    f"{self.provider_id} is selectable "
                    "but is not live"
                )
            if not self.production_image:
                raise CatalogValidationError(
                    f"{self.provider_id} is selectable "
                    "without a production image"
                )

    def to_api_dict(self) -> dict[str, Any]:
        return {
            "providerId": self.provider_id,
            "displayName": self.display_name,
            "ticker": self.ticker,
            "family": self.family,
            "implementation": self.implementation,
            "nodeVersion": self.node_version,
            "network": self.network,
            "miningAlgorithm": self.mining_algorithm,
            "supportedArchitectures": list(
                self.supported_architectures
            ),
            "defaultPorts": self.default_ports,
            "estimatedDiskBytes": (
                self.estimated_disk_bytes
            ),
            "availability": self.availability,
            "selectable": self.selectable,
            "productionImage": self.production_image,
        }


@dataclass(frozen=True)
class ProviderCatalog:
    schema_version: int
    catalog_version: str
    release: str
    frozen: bool
    providers: tuple[ProviderRecord, ...]

    @classmethod
    def load(
        cls,
        path: Path,
    ) -> "ProviderCatalog":
        data = json.loads(path.read_text())

        for key in (
            "schemaVersion",
            "catalogVersion",
            "release",
            "frozen",
            "providers",
        ):
            if key not in data:
                raise CatalogValidationError(
                    f"Catalog is missing {key}"
                )

        providers = tuple(
            ProviderRecord.from_dict(item)
            for item in data["providers"]
        )

        ids = [
            provider.provider_id
            for provider in providers
        ]

        if len(ids) != len(set(ids)):
            raise CatalogValidationError(
                "Catalog contains duplicate provider IDs"
            )

        catalog = cls(
            schema_version=int(
                data["schemaVersion"]
            ),
            catalog_version=str(
                data["catalogVersion"]
            ),
            release=str(data["release"]),
            frozen=bool(data["frozen"]),
            providers=providers,
        )
        catalog.validate()
        return catalog

    def validate(self) -> None:
        live = [
            provider
            for provider in self.providers
            if provider.availability == "live"
        ]

        selectable = [
            provider
            for provider in self.providers
            if provider.selectable
        ]

        if len(live) != 1:
            raise CatalogValidationError(
                "SBP-007 requires exactly one live provider"
            )

        if len(selectable) != 1:
            raise CatalogValidationError(
                "SBP-007 requires exactly one "
                "selectable provider"
            )

        if (
            live[0].provider_id
            != "bitcoin-cash-mainnet"
        ):
            raise CatalogValidationError(
                "Bitcoin Cash must remain the live provider"
            )

    def get(
        self,
        provider_id: str,
    ) -> ProviderRecord:
        for provider in self.providers:
            if provider.provider_id == provider_id:
                return provider

        raise KeyError(provider_id)

    def selectable(self) -> tuple[ProviderRecord, ...]:
        return tuple(
            provider
            for provider in self.providers
            if provider.selectable
        )

    def api_payload(self) -> dict[str, Any]:
        return {
            "schemaVersion": self.schema_version,
            "catalogVersion": self.catalog_version,
            "release": self.release,
            "frozen": self.frozen,
            "providerCount": len(self.providers),
            "liveProviderCount": len(
                [
                    provider
                    for provider in self.providers
                    if provider.availability == "live"
                ]
            ),
            "providers": [
                provider.to_api_dict()
                for provider in self.providers
            ],
        }

    def validate_install_selection(
        self,
        provider_id: str,
        architecture: str,
    ) -> ProviderRecord:
        provider = self.get(provider_id)

        if not provider.selectable:
            raise CatalogValidationError(
                f"{provider.display_name} is not yet "
                "available for installation."
            )

        if architecture not in (
            provider.supported_architectures
        ):
            raise CatalogValidationError(
                f"{provider.display_name} does not "
                f"support {architecture}."
            )

        if not provider.production_image:
            raise CatalogValidationError(
                f"{provider.display_name} has no "
                "production image."
            )

        return provider
