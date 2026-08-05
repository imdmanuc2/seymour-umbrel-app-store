# SBP-006 — BCH Installation Workflow

SBP-006 combines the guarded Umbrel application-control bridge with preflight,
storage validation, state polling, runtime inspection, health probing, and
structured evidence.

The workflow defaults to plan mode. A live install requires the exact
confirmation token `INSTALL-seymour-bch-node`.

Failed installs are not automatically removed. The workflow records a guarded
cleanup recommendation so evidence and logs can be inspected first.
