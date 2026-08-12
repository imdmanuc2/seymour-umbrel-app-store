# SBP-048 — BCH Hardware-Aware IBD Remediation

Purpose
-------

Reduce unnecessary I/O pressure during BCH initial block download on low-memory
hosts by changing the Seymour BCH default transaction index policy from ON to OFF.

Observed on the 1 GB Pi:
- ~905 MiB RAM total
- ~1.5 GiB swap already in use
- 25–49% I/O wait
- very low CPU utilization
- healthy peers available
- txindex enabled and consuming ~1 GiB
- extremely slow IBD throughput

Changes
-------
- provisioning default: txindex OFF
- entrypoint fallback: BCH_TXINDEX default OFF
- provisioning form defaults to OFF
- explicitly provisioned txindex values remain honored
- no prune change
- no chain wipe
- no RPC/ZMQ/port change
- no lifecycle write during install/verify

A guarded BCH restart is required after install.

Disabling txindex does not delete existing txindex data automatically.
