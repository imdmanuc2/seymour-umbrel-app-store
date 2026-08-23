# SBP-075.4 — Native Install Runtime Binding Reconciliation

Integrates canonical runtime storage bindings with the native Umbrel
installation lifecycle.

## Contract

After Umbrel creates the installed app compose:

1. Load canonical runtime binding evidence.
2. Validate provider/app/path identity.
3. Materialize the binding into the installed compose.
4. Report whether the compose changed.
5. Preserve native Umbrel lifecycle ownership.

The reconciler is idempotent. An already-correct compose reports
`changed=false`.

No direct Docker lifecycle operation is introduced.
