# SBP-003 — BCH Fresh Sync Provisioning

SBP-003 makes the fresh-sync workflow executable at the configuration layer.

It persists a validated plan, generates RPC credentials, renders BCHN runtime
configuration, exposes storage and readiness APIs, and prepares the app to begin
synchronization when installed or restarted through Umbrel.
