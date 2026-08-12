# SBP-050 — Nexus Managed Runtime Registration Projection

SBP-050 migrates the existing Blockchain Manager -> Nexus registration payload
toward the SBP-049 canonical managed-runtime contract without creating a second
registration, delivery, scheduler, or lifecycle path.

The existing registration ID, delivery retry/idempotency behavior, scheduler,
evidence files, and HTTP routes remain authoritative.

SBP-050 adds a compatibility-safe `managedRuntimes` projection to the existing
registration payload. Nexus can consume that generic projection while legacy
asset/telemetry fields remain available during the migration.

Safety:
- no lifecycle writes
- no Docker lifecycle commands
- no application restart
- no blockchain configuration change
- no BTC/BCH chain-data operation
