#!/usr/bin/env python3

from pathlib import Path

root = Path(__file__).resolve().parents[3]
app = root / "seymour-blockchain-manager/data/web/app.js"

text = app.read_text()

old_progress = '''function progressBar(value, label) {
  const normalized = Math.max(0, Math.min(Number(value || 0), 100));
  return `
    <div class="progress-row">
      <div><span>${label}</span><strong>${normalized.toFixed(2)}%</strong></div>
      <div class="progress"><i style="width:${normalized}%"></i></div>
    </div>
  `;
}'''

new_progress = '''function formatSyncProgress(value) {
  const numeric = Number(value);

  if (!Number.isFinite(numeric)) return "—";

  const normalized = Math.max(0, Math.min(numeric, 100));

  if (normalized > 0 && normalized < 0.01) {
    return `${normalized.toFixed(4)}%`;
  }

  if (normalized < 1) {
    return `${normalized.toFixed(3)}%`;
  }

  return `${normalized.toFixed(2)}%`;
}

function progressBar(value, label) {
  const normalized = Math.max(0, Math.min(Number(value || 0), 100));
  return `
    <div class="progress-row">
      <div><span>${label}</span><strong>${formatSyncProgress(normalized)}</strong></div>
      <div class="progress"><i style="width:${normalized}%"></i></div>
    </div>
  `;
}'''

if old_progress not in text:
    raise SystemExit("ERROR: progressBar anchor not found")

text = text.replace(old_progress, new_progress, 1)

old_card = '''    const rpcHealthy =
      telemetry.runtimeRpcHealthy ??
      telemetry.rpc?.healthy ??
      telemetry.rpc?.reachable ??
      false;

    return `'''

new_card = '''    const rpcHealthy =
      telemetry.runtimeRpcHealthy ??
      telemetry.rpc?.healthy ??
      telemetry.rpc?.reachable ??
      false;
    const health = runtimeHealthGuidance(telemetry);
    const blockProgress =
      height !== null && headers !== null && headers > 0
        ? `${height.toLocaleString()} / ${headers.toLocaleString()}`
        : "Telemetry warming up";

    return `'''

if old_card not in text:
    raise SystemExit("ERROR: runtime card telemetry anchor not found")

text = text.replace(old_card, new_card, 1)

old_runtime_progress = '''            ? `<div class="runtime-focus-progress">${progressBar(progress, "Blockchain sync")}<div class="runtime-focus-blocks"><span>Blocks</span><strong>${height !== null && headers !== null ? `${height.toLocaleString()} / ${headers.toLocaleString()}` : "Telemetry warming up"}</strong></div></div>`'''

new_runtime_progress = '''            ? `<div class="runtime-focus-progress">${progressBar(progress, "Blockchain sync")}<div class="runtime-focus-blocks"><span>Live block progress</span><strong>${blockProgress}</strong></div><div class="telemetry-grace-note">${health.summary} ${health.detail}</div></div>`'''

if old_runtime_progress not in text:
    raise SystemExit("ERROR: runtime progress markup anchor not found")

text = text.replace(old_runtime_progress, new_runtime_progress, 1)

old_manage_progress = '''      ? `${Number(sync.progressPercent).toFixed(2)}%`
      : "—";'''

new_manage_progress = '''      ? formatSyncProgress(sync.progressPercent)
      : "—";'''

if old_manage_progress not in text:
    raise SystemExit("ERROR: manage progress formatter anchor not found")

text = text.replace(old_manage_progress, new_manage_progress, 1)

app.write_text(text)

print("SBP-064.1 source patch: PASS")
