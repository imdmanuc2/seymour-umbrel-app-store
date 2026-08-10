# SBP-031 — Umbrel App Lifecycle Native Execution Adapter

Target repository: `/home/umbrel/seymour-umbrel-app-store-git`

SBP-031 connects the canonical lifecycle planner introduced by SBP-030 to the
existing native Umbrel application-control bridge.

This package does **not** create a second lifecycle implementation. It composes:

- `shared.app_lifecycle.AppLifecycleEngine` for normalized state/capability planning
- `shared.umbrel_control.UmbrelAppControlBridge` for native Umbrel execution

## Adds

- `LifecycleExecutor`
- normalized before/after lifecycle state
- guarded native execution using the existing confirmation-token contract
- structured lifecycle execution result
- versioned execution contract
- CLI execution plumbing while keeping planning as the default

## Safety

- direct Docker lifecycle remains prohibited
- write actions are never executed unless `--execute` is supplied
- write actions require the exact confirmation token
- verification uses a fake bridge and performs no live lifecycle writes

## Dependency

Requires SBP-030 to be installed first.
