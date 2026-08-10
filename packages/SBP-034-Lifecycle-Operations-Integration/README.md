# SBP-034 — Lifecycle Operations Integration

Adds the canonical Operations-facing lifecycle facade. It composes the already verified lifecycle chain:

SBP-030 planner/state model → SBP-031 native Umbrel executor → SBP-032 result/event projection → SBP-033 best-effort audit persistence.

It does **not** create a second lifecycle executor, does not call Docker lifecycle directly, and defaults to planning only. Live writes still require `execute=True` and the exact SBP-030 confirmation token.

## Installed files

- `shared/app_lifecycle/operations.py`
- `shared/app_lifecycle/__init__.py`
- `shared/contracts/app-lifecycle-operation-v1.json`
- `tests/test_sbp034_operations.py`
- `tests/test_sbp034_contract.py`

Verification uses a fake native bridge and temporary audit storage only.
