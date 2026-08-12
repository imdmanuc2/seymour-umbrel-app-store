# SBP-049 — Canonical Managed Runtime Adapter Contract

Introduces the platform-neutral managed runtime adapter seam used by Nexus,
Blockchain Manager, and future Seymour consumers.

The Umbrel adapter delegates to existing Seymour components:
- `shared.umbrel_runtime.UmbrelRuntime`
- `shared.runtime_state.RuntimeStateService`
- `shared.app_lifecycle.AppLifecycleEngine`
- optional injected `LifecycleOperationService` for guarded writes

SBP-049 does not create a second lifecycle executor and does not perform direct
Docker lifecycle operations.

Contract: `seymour.managed-runtime/1.0`

Installation only changes repository source/contracts. It performs no lifecycle
write, restart, blockchain configuration change, or chain-data operation.
