# SBP-059 — Provider-Neutral BTC/BCH Installer Execution

Generalizes Blockchain Manager's installer from BCH-only execution to BTC + BCH.

Adds provider/app/script mapping, provider-specific confirmation tokens and RPC
environment variables, provider-specific post-install mount verification, and
provider-driven install wizard labels.

Package doctor/install/verify do not execute a live blockchain installation.
