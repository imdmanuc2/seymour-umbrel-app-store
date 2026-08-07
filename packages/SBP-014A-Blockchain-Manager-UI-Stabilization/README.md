# SBP-014A — Blockchain Manager UI Stabilization

Repairs accumulated frontend patch drift in the Seymour Blockchain Manager.

- repairs `renderFilters()`;
- rebuilds `renderProviders()`;
- restores Details, Sync, Adopt, Operations, and Manage buttons;
- restores one event binding per action;
- preserves existing feature functions;
- adds structural regression tests.

No live Umbrel app is restarted and no blockchain operation is executed.
