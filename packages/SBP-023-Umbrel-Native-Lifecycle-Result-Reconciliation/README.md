# SBP-023 — Umbrel Native Lifecycle Result Reconciliation

Purpose:
- improve native Umbrel lifecycle result handling;
- replace opaque lifecycle error reporting;
- add state reconciliation helpers;
- relax BCH sidecar observation timeouts during IBD;
- preserve native API lifecycle semantics.

No live lifecycle action is executed automatically.
