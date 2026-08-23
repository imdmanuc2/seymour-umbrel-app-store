# SBP-075.1.1 — Runtime Binding Shared Projection Repair

Projects the canonical blockchain runtime binding contract into the
Blockchain Manager shared Python tree.

Canonical source:

- shared/blockchain_install/runtime_binding.py

Blockchain Manager projection:

- seymour-blockchain-manager/data/shared/blockchain_install/runtime_binding.py

The two files must remain byte-identical.

This package does not:

- modify runtime bindings
- modify installed compose files
- restart blockchain runtimes
- migrate existing storage
