# SBP-063.3.6 — Hybrid Storage Fresh Install Integration

This package makes the proven Bitcoin Cash hybrid storage layout effective on a **fresh Umbrel installation before the BCH containers are created**.

## Contract

For a remote BCH storage target:

- `/data` remains on local Umbrel app storage.
- `/data/blocks` is bound to the selected remote bulk-storage `blocks` directory.
- Blockchain Manager writes a guarded runtime-binding file into its existing writable evidence mount before invoking Umbrel native install.
- The BCH Umbrel `hooks/pre-install` hook runs host-side after the app files are staged and before Compose starts the runtime. It resolves the portable storage placeholders in the staged `docker-compose.yml`.
- Umbrel remains the canonical lifecycle authority. This package does not add direct Docker lifecycle control.

For a local BCH storage target, the same contract resolves both paths beneath the selected local data path.

## Safety

The installer backs up every file it changes. It does **not** reinstall, stop, restart, or recreate Bitcoin or Bitcoin Cash. It deliberately does not overwrite the currently installed BCH `docker-compose.yml`, because the live runtime already has a proven correct hybrid mount.

After installation, restart **Blockchain Manager only** so its Python process loads the updated installer code. Do not reinstall BCH merely to test this package.
