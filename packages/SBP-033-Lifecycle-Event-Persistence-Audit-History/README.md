# SBP-033 — Lifecycle Event Persistence & Audit History

Target repository: `/home/umbrel/seymour-umbrel-app-store-git`

SBP-033 gives the canonical lifecycle events introduced by SBP-032 a durable,
append-only audit store and a stable history reader.

This package **does not** change native Umbrel execution, lifecycle planning, or
projection. Audit persistence is deliberately best-effort: a storage failure is
reported to the caller but must never turn a successfully completed Umbrel
lifecycle action into an execution failure.

## Adds

- `LifecycleAuditStore`
- `LifecycleAuditRecorder`
- append-only JSONL audit records (`seymour.lifecycle-audit-record/1.0`)
- configurable audit path via `SEYMOUR_LIFECYCLE_AUDIT_PATH`
- default host path: `~/.seymour/lifecycle/audit-events.jsonl`
- durable append with fsync and restrictive file permissions
- history reads with app/action/event/correlation filters
- malformed-record tolerance during history reads
- best-effort persistence result contract

## Boundary

`SBP-030 planner -> SBP-031 native executor -> SBP-032 projection -> SBP-033 audit`

The lifecycle action outcome remains authoritative even if audit persistence is
unavailable. Consumers can inspect the persistence result independently.

## Safety

- direct Docker lifecycle remains prohibited
- doctor/install/verify perform no live Umbrel lifecycle write
- verify writes only to temporary audit files
- runtime audit data is not stored in the Git repository
- no database or Nexus persistence is introduced by this package
