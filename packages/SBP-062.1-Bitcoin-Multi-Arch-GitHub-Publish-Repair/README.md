# SBP-062.1 — Bitcoin Multi-Arch GitHub Publish Repair

Repairs GitHub publishing by building amd64 and arm64 separately, pushing
architecture-specific tags, and publishing the canonical manifest only after
both builds succeed.

No blockchain runtime is restarted and no blockchain data is modified.
