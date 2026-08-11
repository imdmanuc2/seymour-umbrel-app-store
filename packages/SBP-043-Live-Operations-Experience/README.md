# SBP-043 — Live Operations Experience

Frontend-only integration over the existing canonical lifecycle and operations APIs.

Adds a Nexus-style Operations surface for managed blockchain runtimes:

Runtime
- canonical state
- RPC health
- peers
- sync progress

Diagnostics
- run diagnostics
- view recent logs
- lifecycle history

Lifecycle
- plan Start / Stop / Restart through POST /api/lifecycle/operation
- display canonical plan result and required confirmation token
- execute only after explicit browser confirmation
- never use legacy direct lifecycle routes
- never invoke Docker lifecycle directly

Maintenance
- plan backup
- plan restore
- plan upgrade
- guarded backup execution remains supported through the existing operations API

The UI enables/disables lifecycle actions from canonical runtime state:
- syncing/running/degraded -> restart/stop
- stopped/offline -> start
- starting -> stop
- unknown/error follow backend planning contract and fail closed if rejected

No backend code is modified by this package.
