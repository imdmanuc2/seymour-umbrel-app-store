# SBP-063.3.7 — Install Operation Safety & Lifecycle Resilience

Locks the Blockchain Manager install UI during submission, rejects duplicate active installs for the same app, separates short read timeouts from long Umbrel mutation timeouts, and reconciles install timeout/errors against live Umbrel state.

This package does not restart, stop, install, or modify any blockchain runtime.
