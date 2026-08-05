# SBP-005 — Umbrel Application Control Bridge

SBP-005 provides the permanent guarded interface between Seymour and Umbrel's
native application lifecycle API.

Read actions execute immediately. Write actions default to plan mode and require:

1. `--execute`
2. an exact confirmation token such as `INSTALL-seymour-bch-node`

Every executed action produces JSON evidence. Direct Docker lifecycle control is
not used.
