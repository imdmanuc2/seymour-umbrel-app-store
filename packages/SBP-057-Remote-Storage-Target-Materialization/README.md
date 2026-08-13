# SBP-057 — Remote Storage Target Materialization

Adds the first guarded execution path for turning a selected remote storage plan
into a usable Seymour blockchain storage target.

Initial implementation: NFS on trusted LANs.

Capabilities:
- plan a remote NFS target
- validate source/export/mount paths
- create the Seymour blockchain data directory on the storage host
- generate an `/etc/exports.d/seymour-blockchain.exports` fragment
- create the runtime-host mount point
- add an idempotent `/etc/fstab` entry
- mount the target
- verify reachability, writability, filesystem type, and free space
- produce evidence JSON

Safety:
- default mode is plan-only
- execution requires an exact confirmation token
- no blockchain container is stopped/restarted
- no existing blockchain data is moved
- no existing mount is overwritten
- existing non-Seymour fstab/export entries are not edited in place

This package installs the shared materialization engine and CLI only.
`doctor.sh`, `install.sh`, and `verify.sh` do not configure NFS.
