# SBP-075.5 — Native Install Reconciliation Hook

Integrates canonical blockchain runtime binding reconciliation into
the host-side Umbrel install lifecycle.

After a successful native install:

- non-blockchain apps continue normally when no runtime binding exists;
- blockchain runtime binding evidence is reconciled into the installed compose;
- an already-correct compose does not trigger a restart;
- a changed compose triggers a native Umbrel restart;
- restart completion must reach ready/running state;
- reconciliation failures cannot be masked merely because the app is running;
- host, Manager source, and installed Manager control projections remain synchronized.
