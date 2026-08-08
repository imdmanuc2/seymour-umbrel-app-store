# SBP-022 — BCH Runtime Image & Canonical Configuration Reconciliation

Target repository: /home/umbrel/seymour-umbrel-app-store-git
Target branch: master

Purpose:
- reconcile deployed BCH runtime with canonical repository entrypoint;
- ensure generated bitcoin.conf persists RPC allow ranges and credentials;
- prevent recreation from regressing to localhost-only RPC;
- enforce a lightweight healthcheck contract;
- preserve the SBP-021 RPC liveness model.

No live BCH container is recreated automatically.
