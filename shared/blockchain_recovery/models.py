from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any

class RecoveryState(StrEnum):
    HEALTHY="healthy"; RECOVERING="recovering"; BLOCKED="blocked"; DEGRADED="degraded"

class RecoveryKind(StrEnum):
    STORAGE_MOUNT_MISSING="storage-mount-missing"
    STORAGE_BINDING_MISMATCH="storage-binding-mismatch"
    DNS_ALIAS_COLLISION="dns-alias-collision"
    STARTUP_WARMUP="startup-warmup"
    REGISTRATION_MISSING="registration-missing"
    SUSPICIOUS_FRESH_SYNC="suspicious-fresh-sync"

@dataclass
class Finding:
    kind: RecoveryKind
    state: RecoveryState
    message: str
    repairable: bool=False
    confirmation: str|None=None
    evidence: dict[str,Any]=field(default_factory=dict)
    def to_dict(self):
        d=asdict(self); d["kind"]=self.kind.value; d["state"]=self.state.value; return d

@dataclass
class RecoveryReport:
    provider_id: str
    runtime_host: str
    state: RecoveryState
    findings: list[Finding]
    executed: bool=False
    success: bool|None=None
    steps: list[dict[str,Any]]=field(default_factory=list)
    def to_dict(self):
        return {"contract":"seymour.blockchain-runtime-recovery","version":"1.0",
        "providerId":self.provider_id,"runtimeHost":self.runtime_host,
        "state":self.state.value,"executed":self.executed,"success":self.success,
        "findings":[f.to_dict() for f in self.findings],"steps":self.steps}
