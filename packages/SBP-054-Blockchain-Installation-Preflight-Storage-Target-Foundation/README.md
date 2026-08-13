# SBP-054 — Blockchain Installation Preflight & Storage Target Foundation

Provider-neutral install preflight and storage-target foundation for Seymour blockchain runtimes.

Adds:
- runtime-host inventory
- local / attached / remote storage target model
- explicit storage selection contract
- capacity safety reserve
- writable / reachable / persistent storage checks
- common provider-neutral preflight result

Does not install, stop, restart, move, or reconfigure any blockchain runtime.
Does not configure NFS/SMB yet.
