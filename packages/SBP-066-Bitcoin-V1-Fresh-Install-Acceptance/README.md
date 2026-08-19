# SBP-066 — Bitcoin V1 Fresh-Install Acceptance

Purpose: provide a non-destructive Version 1.0 acceptance gate for the Bitcoin
managed-runtime installation path.

This package does not install, stop, restart, recreate, update, or uninstall any
blockchain runtime.

Acceptance coverage:
- Bitcoin provider catalog install contract exists.
- Bitcoin install workflow and common blockchain-install modules compile.
- Canonical Bitcoin compose remains provider-neutral.
- Bitcoin pre-install hook derives RPC/status DNS identities from the installed app id.
- Isolated fresh-install staging materializes runtime-specific DNS identities without
  touching the live installation.
- Isolated runtime binding persistence resolves `/data` and `/node-data` storage anchors.
- Fixed Docker container-name assumptions are prohibited from Manager BTC discovery.
- Live Bitcoin is running/healthy with zero restart churn.
- Live Bitcoin status service reports Bitcoin Core telemetry, not BCH telemetry.
- Blockchain Manager projects Bitcoin as installed/running and consumes live status data.
- Bitcoin Cash remains running/healthy.

The existing live Bitcoin dataset is explicitly outside this package's mutation scope.
