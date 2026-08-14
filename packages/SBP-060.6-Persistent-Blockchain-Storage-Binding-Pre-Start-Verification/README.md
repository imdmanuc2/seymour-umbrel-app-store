# SBP-060.6 — Persistent Blockchain Storage Binding & Pre-Start Verification

Purpose: prevent a managed blockchain runtime from silently falling back to local
app-data when an external blockchain data path was selected.

This package:
- persists the selected blockchain data path into installed Compose
- verifies the live `/data` mount matches the expected canonical path
- fails closed on binding mismatch
- is provider-neutral for BCH/BTC/future runtimes
- does not restart runtimes or move/delete blockchain data
