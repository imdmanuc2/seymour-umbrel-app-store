# SBP-074 — Monero Persistent Storage Binding & First-Install Preflight

Prepares Monero persistent storage before first install.

The package:
- adds a provider-neutral runtime storage provisioning helper;
- derives the provider directory from the provider catalog;
- derives runtime UID/GID from the Umbrel data root;
- creates the provider directory on the selected storage root;
- persists Monero runtime binding evidence;
- extends the Monero pre-install hook to materialize `/data`, `/node-data`,
  RPC identity, and status identity into the installed Compose file.

This package does not install or start Monero and does not modify BTC/BCH runtimes.
