# SBP-032 — Canonical Lifecycle Result & Event Projection

Target repository: `/home/umbrel/seymour-umbrel-app-store-git`

SBP-032 projects the guarded native lifecycle execution result introduced by
SBP-031 into stable platform-facing contracts.

This package adds **projection only**. It does not add persistence, a second
execution path, direct Docker lifecycle, or UI behavior.

## Adds

- `LifecycleResultProjector`
- canonical lifecycle result payload (`seymour.lifecycle-result/1.0`)
- canonical lifecycle event payload (`seymour.lifecycle-event/1.0`)
- correlation IDs for result/event pairing
- normalized state/result/error/evidence fields
- deterministic event classification for planned, rejected, succeeded, and failed actions

## Boundary

`SBP-030 planner -> SBP-031 native executor -> SBP-032 projection`

Consumers such as Blockchain Manager, Nexus CMDB, Operations, Timeline, and
future UI code should consume the canonical projection rather than parsing the
native Umbrel operation payload.

## Safety

- direct Docker lifecycle remains prohibited
- no live lifecycle action is executed by doctor/install/verify
- native operation details remain opaque evidence
- persistence is intentionally deferred to the next package
