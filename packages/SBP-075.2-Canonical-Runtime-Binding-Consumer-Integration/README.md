# SBP-075.2 — Canonical Runtime Binding Consumer Integration

Integrates the canonical RuntimeBinding contract into the
Blockchain Manager installation workflow.

The installer now:

- constructs one canonical RuntimeBinding per installation
- uses RuntimeBinding.environment() for install environment values
- persists runtime binding evidence using serialize_runtime_binding()
- writes binding evidence for all supported blockchain providers
- uses single-path mode for normal runtimes
- uses hybrid-blocks mode for remote Bitcoin Cash storage
- removes duplicate manual runtime storage environment construction

This package does not restart, stop, reinstall, or modify any live
blockchain runtime.
