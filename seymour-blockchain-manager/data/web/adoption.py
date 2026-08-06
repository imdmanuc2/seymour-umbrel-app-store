from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import StrEnum
import json
import os
from pathlib import Path
import shutil
from typing import Any
from uuid import uuid4

MANAGED_DATA_PATH = Path(os.environ.get("BCH_MANAGED_DATA_PATH", "/adopted-bch-data"))
EVIDENCE_PATH = Path(os.environ.get("ADOPTION_EVIDENCE_PATH", "/evidence/adoptions.jsonl"))
PLANS_PATH = Path(os.environ.get("ADOPTION_PLAN_DIRECTORY", "/evidence/adoption-plans"))
APP_ID = os.environ.get("BCH_APP_ID", "seymour-bch-node")
PROVIDER_ID = "bitcoin-cash-mainnet"
CONFIRMATION_TOKEN = f"ADOPT-{APP_ID}"

class AdoptionStatus(StrEnum):
    PLANNED = "planned"
    SUCCEEDED = "succeeded"
    FAILED = "failed"

@dataclass
class AdoptionPlan:
    operation_id: str
    source_path: str
    destination_path: str
    provider_id: str
    app_id: str
    status: AdoptionStatus
    created_at: str
    validation: dict[str, Any]
    required_confirmation: str
    result: dict[str, Any] | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data

def utc_now() -> str:
    return datetime.now(UTC).isoformat()

def directory_size(path: Path) -> int:
    total = 0
    if not path.exists():
        return 0
    for item in path.rglob("*"):
        try:
            if item.is_file():
                total += item.stat().st_size
        except OSError:
            continue
    return total

def validate_source(path: Path) -> dict[str, Any]:
    checks = {
        "exists": path.is_dir(),
        "blocksDirectory": (path / "blocks").is_dir(),
        "chainstateDirectory": (path / "chainstate").is_dir(),
        "walletsDetected": (path / "wallets").exists(),
        "sizeBytes": directory_size(path),
    }
    errors: list[str] = []
    if not checks["exists"]:
        errors.append("Source directory does not exist.")
    if checks["exists"] and not checks["blocksDirectory"]:
        errors.append("Source does not contain a blocks directory.")
    if checks["exists"] and not checks["chainstateDirectory"]:
        errors.append("Source does not contain a chainstate directory.")
    return {"valid": not errors, "checks": checks, "errors": errors}

def destination_state(path: Path) -> dict[str, Any]:
    exists = path.exists()
    populated = False
    if exists:
        try:
            populated = any(path.iterdir())
        except OSError:
            populated = True
    return {
        "path": str(path),
        "exists": exists,
        "populated": populated,
        "sizeBytes": directory_size(path),
    }

class AdoptionService:
    def __init__(self, destination: Path = MANAGED_DATA_PATH, evidence_path: Path = EVIDENCE_PATH, plans_path: Path = PLANS_PATH) -> None:
        self.destination = destination
        self.evidence_path = evidence_path
        self.plans_path = plans_path

    def _save(self, plan: AdoptionPlan) -> None:
        self.plans_path.mkdir(parents=True, exist_ok=True)
        (self.plans_path / f"{plan.operation_id}.json").write_text(json.dumps(plan.to_dict(), indent=2))
        self.evidence_path.parent.mkdir(parents=True, exist_ok=True)
        with self.evidence_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(plan.to_dict(), sort_keys=True) + "\n")

    def load(self, operation_id: str) -> dict[str, Any]:
        path = self.plans_path / f"{operation_id}.json"
        if not path.is_file():
            raise KeyError(operation_id)
        return json.loads(path.read_text())

    def plan(self, source: Path) -> AdoptionPlan:
        source_validation = validate_source(source)
        destination = destination_state(self.destination)
        if destination["populated"]:
            source_validation["valid"] = False
            source_validation["errors"].append("Managed destination is populated; overwrite is forbidden.")
        plan = AdoptionPlan(
            operation_id=str(uuid4()),
            source_path=str(source),
            destination_path=str(self.destination),
            provider_id=PROVIDER_ID,
            app_id=APP_ID,
            status=AdoptionStatus.PLANNED,
            created_at=utc_now(),
            validation={"source": source_validation, "destination": destination},
            required_confirmation=CONFIRMATION_TOKEN,
        )
        self._save(plan)
        return plan

    def execute(self, operation_id: str, confirmation: str) -> AdoptionPlan:
        raw = self.load(operation_id)
        plan = AdoptionPlan(
            operation_id=raw["operation_id"],
            source_path=raw["source_path"],
            destination_path=raw["destination_path"],
            provider_id=raw["provider_id"],
            app_id=raw["app_id"],
            status=AdoptionStatus(raw["status"]),
            created_at=raw["created_at"],
            validation=raw["validation"],
            required_confirmation=raw["required_confirmation"],
            result=raw.get("result"),
            error=raw.get("error"),
        )
        if confirmation != plan.required_confirmation:
            plan.status = AdoptionStatus.FAILED
            plan.error = "Adoption confirmation token did not match."
            self._save(plan)
            return plan
        if not plan.validation["source"]["valid"]:
            plan.status = AdoptionStatus.FAILED
            plan.error = "Source validation failed."
            self._save(plan)
            return plan
        if plan.validation["destination"]["populated"]:
            plan.status = AdoptionStatus.FAILED
            plan.error = "Managed destination is populated."
            self._save(plan)
            return plan
        source = Path(plan.source_path)
        destination = Path(plan.destination_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            if destination.exists():
                destination.rmdir()
            shutil.copytree(source, destination)
            verification = validate_source(destination)
            plan.result = {
                "copied": True,
                "verification": verification,
                "sourceSizeBytes": directory_size(source),
                "destinationSizeBytes": directory_size(destination),
            }
            plan.status = AdoptionStatus.SUCCEEDED if verification["valid"] else AdoptionStatus.FAILED
            if plan.status is AdoptionStatus.FAILED:
                plan.error = "Post-adoption verification failed."
        except Exception as exc:
            plan.status = AdoptionStatus.FAILED
            plan.error = str(exc)
        self._save(plan)
        return plan
