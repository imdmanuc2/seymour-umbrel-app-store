# SBP-013 — Snapshot Import and Existing Node Adoption

Adds guarded adoption of an existing Bitcoin Cash datadir or imported snapshot.

The package detects and validates existing chain data, refuses destructive overwrite, creates an adoption plan, requires an explicit confirmation token, records evidence, and performs post-adoption verification.

Verification never alters a live BCH datadir.
