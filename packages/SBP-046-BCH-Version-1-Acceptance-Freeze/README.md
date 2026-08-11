# SBP-046 — BCH Version 1 Acceptance & Freeze

Read-only acceptance milestone for the Bitcoin Cash provider/runtime.

Purpose
-------

Prove the full BCH provider path is production-ready enough to freeze as the
reference implementation for future blockchain runtimes.

This package does NOT:
- install new features
- change runtime state
- restart/stop/start any Umbrel app
- execute lifecycle writes
- modify Docker lifecycle
- redesign the UI

Acceptance scope
----------------

1. Umbrel lifecycle state
2. BCH node container health
3. Direct BCH RPC
4. Canonical runtime state
5. Sync telemetry
6. Status service
7. Blockchain Manager dashboard contract
8. Operations diagnostics
9. Operations logs
10. Lifecycle planning
11. Lifecycle history/audit
12. Nexus runtime projection anchors
13. Frontend contract
14. No duplicate state inference
15. No direct Docker lifecycle paths

Freeze criteria
---------------

When verify.sh passes:
- BCH becomes the reference provider baseline.
- Future providers should conform to the same contracts.
- BCH-specific feature work stops unless a defect is found.
