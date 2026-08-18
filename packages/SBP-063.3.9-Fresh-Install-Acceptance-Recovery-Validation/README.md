# SBP-063.3.9 — Fresh Install Acceptance & Recovery Validation

Purpose: provide a non-destructive Version 1.0 acceptance gate for the BCH fresh-install,
hybrid-storage, install-safety, lifecycle-timeout, telemetry, and recovery contracts
introduced in SBP-063.3.6 through SBP-063.3.8.

This package does not install, stop, restart, recreate, or uninstall any blockchain runtime.

Acceptance coverage:
- portable BCH hybrid compose anchors exist;
- the BCH pre-install hook resolves all four hybrid storage mounts in an isolated staging tree;
- install-operation duplicate guard remains present;
- split lifecycle timeout/reconciliation contracts remain present;
- live BCH is running/healthy with zero restart churn;
- live /data/blocks is bound to the Seymour remote storage path;
- fresh local chainstate and remote block/index files exist;
- recent BCH logs contain sustained progress and no fatal block/index consistency errors;
- Bitcoin remains running and healthy.

Recovery directories are intentionally left untouched by this package.
