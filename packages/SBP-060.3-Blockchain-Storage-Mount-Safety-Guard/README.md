# SBP-060.3 — Blockchain Storage Mount Safety Guard

Adds fail-closed storage identity validation before Seymour creates blockchain data directories or executes a blockchain installation.

The guard verifies the selected target still exists, is backed by the expected mount, attached/remote targets remain real mount points, filesystem/source/UUID identity matches when available, the target is writable, required free capacity exists, and the provider data path remains contained beneath the verified target.

This prevents a missing external/remote mount from silently falling back to the runtime host root filesystem.

Package install/verify do not start, stop, restart, or move blockchain data.
