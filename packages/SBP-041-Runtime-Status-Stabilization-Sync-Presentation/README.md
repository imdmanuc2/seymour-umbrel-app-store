# SBP-041 — Runtime Status Stabilization & Sync Presentation

Purpose
-------

Prevent the Blockchain Manager BCH card from flapping between `Syncing` and
`Degraded` during short RPC/telemetry gaps while initial block download is
actively progressing.

Important boundary:

- Canonical backend runtime state is NOT changed or delayed.
- Lifecycle/Nexus still receive the immediate canonical state.
- Stabilization exists only in the Blockchain Manager browser presentation.
- A short grace window holds the last good `syncing` display.
- Sustained degraded/error/offline conditions are shown normally after grace.
- Live metrics use the last good values only during the short grace window.

Default grace window: 20 seconds.

The card also strengthens the sync status presentation:
- prominent `Syncing` pill
- thicker progress bar
- `blocks / headers` progress context
- explicit RPC state
- visible "telemetry reconnecting" note only during a grace-held state

No lifecycle writes are performed.
