# SBP-055 — Blockchain Installer Storage Target Selection

Connects SBP-054 storage targets to Blockchain Manager's installation flow.

Adds:
- storage-target inventory service
- `/api/install/storage-targets`
- explicit storage-target choice in the existing install wizard
- selected target carried into the install request
- preflight against the selected target

This package does not configure NFS/SMB, move chain data, or touch running runtimes.
