# SBP-064 — Blockchain Runtime Health & Recovery Guidance

Purpose: integrate existing runtime state, sync analysis, diagnostics, and lifecycle capabilities into a provider-neutral operator-facing health/recovery guidance contract.

Scope:
- add a provider-neutral runtime health projection contract;
- map runtime/sync/storage/RPC conditions to structured health state, reason code, summary, detail, recommended action, and destructive flag;
- expose health guidance in the Blockchain Manager dashboard payload;
- render health guidance in Manage and Operations Center UI;
- reuse existing diagnostics/logs/lifecycle actions;
- no automatic destructive repair.

Safety: package installation does not install, stop, start, restart, recreate, or uninstall blockchain runtimes.
