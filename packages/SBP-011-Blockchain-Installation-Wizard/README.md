# SBP-011 — Blockchain Installation Wizard

Adds a guarded, catalog-driven Bitcoin Cash installation wizard to the Seymour Blockchain Manager.

The package adds preflight validation, secure RPC credential generation, configuration review, confirmation-token enforcement, execution through the existing `seymour-install-bch` workflow, operation evidence, and post-install verification.

Verification does not install or restart a live blockchain node.
