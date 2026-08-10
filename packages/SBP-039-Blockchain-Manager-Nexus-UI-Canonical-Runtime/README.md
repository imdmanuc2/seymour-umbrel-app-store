# SBP-039 — Blockchain Manager Nexus UI & Canonical Runtime Integration

First frontend milestone after the lifecycle/runtime backend foundation.

- Canonical runtimeState wins over legacy lifecycleStatus.
- Adds starting/syncing/running/degraded/stopped/offline/error labels.
- Replaces overflowing BCH action row with Open / Operations / Manage.
- Rebuilds Management around canonical runtime state and live telemetry.
- Adds Nexus-style framed shell, panel hierarchy, cards, status pills, modal,
  spacing, and responsive behavior.
- Synchronizes changed static assets into Umbrel app-data when present.

No backend state inference is added and no lifecycle write is executed.
