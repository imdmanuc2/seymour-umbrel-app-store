from pathlib import Path
import sys

root = Path(sys.argv[1])
css_payload = Path(sys.argv[2])
js = root / "seymour-blockchain-manager/data/web/app.js"
css = root / "seymour-blockchain-manager/data/web/style.css"

s = js.read_text()

old = '''function lifecycle(provider) {
  const telemetry = providerTelemetry(provider.providerId);
  if (provider.availability !== "live") return "coming-soon";
  return telemetry?.lifecycleStatus || "unknown";
}
'''
new = '''function lifecycle(provider) {
  const telemetry = providerTelemetry(provider.providerId);
  if (provider.availability !== "live") return "coming-soon";

  const canonical =
    telemetry?.runtimeState ||
    telemetry?.operationalState?.state ||
    telemetry?.runtime?.runtimeState;

  if (canonical) return canonical;

  // Compatibility fallback only. Canonical runtime state takes precedence.
  return telemetry?.lifecycleStatus || "unknown";
}
'''
if old in s:
    s = s.replace(old, new, 1)
elif "telemetry?.runtimeState" not in s:
    raise SystemExit("SBP-039 patch: lifecycle() anchor not found")

label_old = '''    "running": "Running",
    "syncing": "Syncing",
    "stopped": "Stopped",
    "error": "Error",
'''
label_new = '''    "running": "Running",
    "syncing": "Syncing",
    "starting": "Starting",
    "degraded": "Degraded",
    "stopped": "Stopped",
    "offline": "Offline",
    "error": "Error",
'''
if label_old in s:
    s = s.replace(label_old, label_new, 1)

# Replace provider action rendering with a stable three-button footer.
action_start = s.find('        <div class="card-actions">')
action_end = s.find('        </div>\n      </article>', action_start)
if action_start < 0 or action_end < 0:
    raise SystemExit("SBP-039 patch: provider card actions block not found")
action_end += len('        </div>')

new_actions = '''        <div class="card-actions">
          ${
            provider.selectable
              ? `
                <button class="secondary" data-details="${provider.providerId}">
                  Open
                </button>
                <button class="secondary" data-operations="${provider.providerId}">
                  Operations
                </button>
                <button class="primary" data-manage="${provider.providerId}">
                  Manage
                </button>
              `
              : `
                <button class="secondary" data-details="${provider.providerId}">
                  View details
                </button>
                <button class="disabled" disabled>Coming soon</button>
              `
          }
        </div>'''
s = s[:action_start] + new_actions + s[action_end:]

start = s.find("function showManage(providerId) {")
end = s.find("\nasync function loadCatalog()", start)
if start < 0 or end < 0:
    raise SystemExit("SBP-039 patch: showManage() anchors not found")

manage = r'''function showManage(providerId) {
  const provider = state.providers.find(
    (item) => item.providerId === providerId
  );
  const telemetry = providerTelemetry(providerId) || {};
  const runtimeState = lifecycle(provider);
  const sync = telemetry.sync || {};
  const progress =
    sync.progressPercent !== null && sync.progressPercent !== undefined
      ? `${Number(sync.progressPercent).toFixed(2)}%`
      : "—";

  dialogContent.innerHTML = `
    <p class="provider-family">management</p>
    <h2>${provider.displayName}</h2>

    <div class="runtime-banner">
      <strong>
        <span class="runtime-state-dot ${runtimeState}"></span>
        ${lifecycleLabel(runtimeState)}
      </strong>
      <span>${runtimeState === "syncing" ? progress + " verified" : "Canonical runtime state"}</span>
    </div>

    <div class="manage-grid">
      <article><span>RPC</span><strong>${telemetry.rpc?.reachable ? "Healthy" : "Unavailable"}</strong></article>
      <article><span>Height</span><strong>${sync.height ?? "—"}</strong></article>
      <article><span>Headers</span><strong>${sync.headers ?? "—"}</strong></article>
      <article><span>Peers</span><strong>${telemetry.peers ?? "—"}</strong></article>
      <article><span>Chain data</span><strong>${formatBytes(telemetry.data?.usedBytes)}</strong></article>
      <article><span>App ID</span><strong>${provider.installAction?.appId || "—"}</strong></article>
    </div>

    <div class="manage-actions">
      <button class="secondary" id="manageSync">Sync</button>
      <button class="secondary" id="manageOperations">Operations</button>
      <button class="secondary" id="manageAdopt">Adopt</button>
    </div>
  `;

  document.getElementById("manageSync")?.addEventListener("click", () => {
    dialog.close();
    showSyncManager(providerId);
  });
  document.getElementById("manageOperations")?.addEventListener("click", () => {
    dialog.close();
    showOperationsCenter(providerId);
  });
  document.getElementById("manageAdopt")?.addEventListener("click", () => {
    dialog.close();
    showAdoptionWizard(providerId);
  });

  dialog.showModal();
}
'''
s = s[:start] + manage + s[end:]
js.write_text(s)

css_text = css.read_text()
marker = "/* SBP-039 — Nexus visual integration */"
if marker not in css_text:
    css_text += "\n\n" + css_payload.read_text() + "\n"
css.write_text(css_text)