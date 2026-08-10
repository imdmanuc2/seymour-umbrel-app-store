from pathlib import Path
import sys

root = Path(sys.argv[1])
js = root / "seymour-blockchain-manager/data/web/app.js"
html = root / "seymour-blockchain-manager/data/web/index.html"
css = root / "seymour-blockchain-manager/data/web/style.css"

s = js.read_text()

# ---------------------------------------------------------------------------
# Operational summary projection
# ---------------------------------------------------------------------------
if "function renderOperationalSummary()" not in s:
    anchor = "function renderHost() {"
    idx = s.find(anchor)
    if idx < 0:
        raise SystemExit("SBP-042 patch: renderHost anchor missing")

    helper = r'''function installedProviders() {
  return state.providers.filter(
    (provider) => provider.availability === "live"
  );
}

function plannedProviders() {
  return state.providers.filter(
    (provider) => provider.availability !== "live"
  );
}

function renderOperationalSummary() {
  const live = installedProviders();
  const presentations = live.map((provider) => ({
    provider,
    presentation: presentedRuntime(provider),
  }));

  const syncing = presentations.filter(
    ({presentation}) => presentation.state === "syncing"
  ).length;
  const running = presentations.filter(
    ({presentation}) => presentation.state === "running"
  ).length;
  const degraded = presentations.filter(
    ({presentation}) => presentation.state === "degraded"
  ).length;

  const rpcReachable = presentations.filter(({presentation}) => {
    const telemetry = presentation.telemetry || {};
    return Boolean(
      telemetry.runtimeRpcReachable ??
      telemetry.rpc?.reachable
    );
  }).length;

  const peers = presentations.reduce((sum, {presentation}) => {
    return sum + Number(presentation.telemetry?.peers || 0);
  }, 0);

  const diskBytes = presentations.reduce((sum, {presentation}) => {
    return sum + Number(
      presentation.telemetry?.data?.usedBytes || 0
    );
  }, 0);

  const values = {
    installedCount: live.length,
    syncingCount: syncing,
    runningCount: running,
    rpcReachableCount: rpcReachable,
    peerCount: peers,
    runtimeDiskUsed: formatBytes(diskBytes),
    degradedCount: degraded,
  };

  Object.entries(values).forEach(([id, value]) => {
    const node = document.getElementById(id);
    if (node) node.textContent = value;
  });
}

function renderRuntimeFocus() {
  const target = document.getElementById("runtimeFocus");
  if (!target) return;

  const live = installedProviders();
  if (!live.length) {
    target.innerHTML = `
      <div class="empty-runtime-focus">
        No managed blockchain runtime is currently installed.
      </div>
    `;
    return;
  }

  const provider = live[0];
  const presentation = presentedRuntime(provider);
  const telemetry = presentation.telemetry || {};
  const sync = telemetry.sync || {};
  const stateLabel = lifecycleLabel(presentation.state);
  const progress = Number(sync.progressPercent || 0);
  const height = sync.height ?? "—";
  const headers = sync.headers ?? "—";
  const peers = telemetry.peers ?? "—";
  const rpcHealthy =
    telemetry.runtimeRpcHealthy ??
    telemetry.rpc?.healthy ??
    telemetry.rpc?.reachable ??
    false;

  target.innerHTML = `
    <article class="runtime-focus-card ${presentation.state}">
      <div class="runtime-focus-heading">
        <div>
          <p class="provider-family">managed runtime</p>
          <h2>${provider.displayName}</h2>
          <p class="implementation">
            ${provider.implementation} ${provider.nodeVersion}
          </p>
        </div>
        <span class="status-pill">${stateLabel}</span>
      </div>

      ${
        presentation.state === "syncing"
          ? `
            <div class="runtime-focus-progress">
              ${progressBar(progress, "Blockchain sync")}
              <div class="runtime-focus-blocks">
                <span>Blocks</span>
                <strong>${Number(height).toLocaleString()} / ${Number(headers).toLocaleString()}</strong>
              </div>
            </div>
          `
          : ""
      }

      <div class="runtime-focus-kpis">
        <article><span>Runtime</span><strong>${stateLabel}</strong></article>
        <article><span>RPC</span><strong class="${rpcHealthy ? "metric-good" : "metric-bad"}">${rpcHealthy ? "Healthy" : "Unavailable"}</strong></article>
        <article><span>Peers</span><strong>${peers}</strong></article>
        <article><span>Chain data</span><strong>${formatBytes(telemetry.data?.usedBytes)}</strong></article>
      </div>

      <div class="runtime-focus-actions">
        <button class="secondary" data-focus-details="${provider.providerId}">Open</button>
        <button class="secondary" data-focus-operations="${provider.providerId}">Operations</button>
        <button class="primary" data-focus-manage="${provider.providerId}">Manage</button>
      </div>
    </article>
  `;

  target.querySelector("[data-focus-details]")?.addEventListener(
    "click",
    () => showDetails(provider.providerId)
  );
  target.querySelector("[data-focus-operations]")?.addEventListener(
    "click",
    () => showOperationsCenter(provider.providerId)
  );
  target.querySelector("[data-focus-manage]")?.addEventListener(
    "click",
    () => showManage(provider.providerId)
  );
}

'''
    s = s[:idx] + helper + s[idx:]

# Render provider catalog as future-only cards in the normal grid.
start = s.find("function renderProviders() {")
end = s.find("\nfunction showDetails", start)
if start < 0 or end < 0:
    raise SystemExit("SBP-042 patch: renderProviders anchors missing")

render_providers = r'''function renderProviders() {
  const providers = filteredProviders().filter(
    (provider) => provider.availability !== "live"
  );

  grid.innerHTML = providers.map((provider) => {
    return `
      <article class="provider-card catalog-card ${provider.availability}">
        <div class="card-top">
          <div class="coin-badge">${provider.ticker}</div>
          <span class="status-pill">Coming soon</span>
        </div>
        <div>
          <p class="provider-family">${provider.family}</p>
          <h2>${provider.displayName}</h2>
          <p class="implementation">
            ${provider.implementation} ${provider.nodeVersion}
          </p>
        </div>
        <dl class="metadata">
          <div><dt>Mining</dt><dd>${provider.miningAlgorithm}</dd></div>
          <div><dt>Disk estimate</dt><dd>${formatBytes(provider.estimatedDiskBytes)}</dd></div>
          <div><dt>Architecture</dt><dd>${provider.supportedArchitectures.join(" · ")}</dd></div>
        </dl>
        <div class="card-actions catalog-actions">
          <button class="secondary" data-details="${provider.providerId}">
            View details
          </button>
          <button class="disabled" disabled>Coming soon</button>
        </div>
      </article>
    `;
  }).join("");

  grid.querySelectorAll("[data-details]").forEach((button) => {
    button.addEventListener("click", () => {
      showDetails(button.dataset.details);
    });
  });
}
'''
s = s[:start] + render_providers + s[end:]

# Add focus/summary refresh after telemetry update.
old = '''    state.telemetry = await response.json();
    renderHost();
    renderProviders();
'''
new = '''    state.telemetry = await response.json();
    renderHost();
    renderOperationalSummary();
    renderRuntimeFocus();
    renderProviders();
'''
if old in s:
    s = s.replace(old, new, 1)
elif "renderRuntimeFocus();" not in s:
    raise SystemExit("SBP-042 patch: refreshTelemetry anchor missing")

js.write_text(s)

# ---------------------------------------------------------------------------
# index.html: replace catalog summary with operational summary + runtime focus
# ---------------------------------------------------------------------------
h = html.read_text()

summary_start = h.find('<section class="summary">')
summary_end = h.find('</section>', summary_start)
if summary_start < 0 or summary_end < 0:
    raise SystemExit("SBP-042 patch: summary section anchor missing")
summary_end += len("</section>")

summary = '''<section class="summary operational-summary">
        <article>
          <span class="summary-label">Installed nodes</span>
          <strong id="installedCount">0</strong>
        </article>
        <article>
          <span class="summary-label">Syncing</span>
          <strong id="syncingCount">0</strong>
        </article>
        <article>
          <span class="summary-label">Running</span>
          <strong id="runningCount">0</strong>
        </article>
        <article>
          <span class="summary-label">RPC reachable</span>
          <strong id="rpcReachableCount">0</strong>
        </article>
        <article>
          <span class="summary-label">Peers</span>
          <strong id="peerCount">0</strong>
        </article>
        <article>
          <span class="summary-label">Runtime disk</span>
          <strong id="runtimeDiskUsed">—</strong>
        </article>
      </section>

      <section class="runtime-section">
        <div class="section-heading">
          <div>
            <p class="eyebrow">Operational focus</p>
            <h2>Managed blockchains</h2>
          </div>
          <span class="section-note">Live canonical runtime state</span>
        </div>
        <div id="runtimeFocus"></div>
      </section>'''

h = h[:summary_start] + summary + h[summary_end:]

# Add catalog heading before toolbar if missing.
toolbar_anchor = '<section class="toolbar">'
if '<p class="eyebrow">Provider catalog</p>' not in h:
    idx = h.find(toolbar_anchor)
    if idx < 0:
        raise SystemExit("SBP-042 patch: toolbar anchor missing")
    heading = '''<section class="catalog-heading">
        <div>
          <p class="eyebrow">Provider catalog</p>
          <h2>Available next</h2>
          <p>Explore planned blockchain runtimes without distracting from live operations.</p>
        </div>
      </section>

      '''
    h = h[:idx] + heading + h[idx:]

html.write_text(h)

# ---------------------------------------------------------------------------
# CSS additions
# ---------------------------------------------------------------------------
c = css.read_text()
marker = "/* SBP-042 — Nexus experience */"
if marker not in c:
    c += r'''

/* SBP-042 — Nexus experience */
.operational-summary {
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 18px;
}

.operational-summary article {
  min-height: 92px;
  padding: 15px 16px;
}

.operational-summary strong {
  font-size: 26px;
}

.runtime-section {
  margin-bottom: 22px;
  padding: 18px;
  border: 1px solid rgba(83,145,224,.24);
  border-radius: 18px;
  background: rgba(7,18,34,.82);
}

.section-heading,
.runtime-focus-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
}

.section-heading {
  margin-bottom: 14px;
}

.section-heading h2,
.catalog-heading h2 {
  margin-bottom: 4px;
}

.section-note,
.catalog-heading p {
  color: var(--muted);
  font-size: 12px;
}

.runtime-focus-card {
  padding: 22px;
  border: 1px solid rgba(77,156,255,.32);
  border-radius: 16px;
  background:
    radial-gradient(circle at 100% 0%, rgba(77,156,255,.13), transparent 38%),
    rgba(10,27,46,.94);
}

.runtime-focus-card.syncing {
  border-color: rgba(77,156,255,.55);
}

.runtime-focus-card.running {
  border-color: rgba(67,217,155,.48);
}

.runtime-focus-card.degraded {
  border-color: rgba(243,155,88,.48);
}

.runtime-focus-progress {
  margin-top: 18px;
  padding: 14px 16px;
  border: 1px solid rgba(77,156,255,.18);
  border-radius: 13px;
  background: rgba(4,15,28,.56);
}

.runtime-focus-progress .progress {
  height: 14px;
}

.runtime-focus-blocks {
  display: flex;
  justify-content: space-between;
  margin-top: 9px;
  color: var(--muted);
  font-size: 12px;
}

.runtime-focus-blocks strong {
  color: var(--text);
}

.runtime-focus-kpis {
  display: grid;
  grid-template-columns: repeat(4, minmax(0,1fr));
  gap: 10px;
  margin-top: 15px;
}

.runtime-focus-kpis article {
  padding: 13px 14px;
  border: 1px solid rgba(83,145,224,.17);
  border-radius: 12px;
  background: rgba(5,17,31,.72);
}

.runtime-focus-kpis span {
  display: block;
  margin-bottom: 5px;
  color: var(--muted);
  font-size: 11px;
}

.runtime-focus-actions {
  display: flex;
  justify-content: flex-end;
  gap: 9px;
  margin-top: 16px;
}

.runtime-focus-actions button {
  min-width: 112px;
  padding: 10px 14px;
  border: 1px solid rgba(83,145,224,.28);
  border-radius: 10px;
  background: rgba(12,34,56,.95);
  color: var(--text);
  cursor: pointer;
}

.runtime-focus-actions .primary {
  background: #1a67b6;
  border-color: rgba(80,155,237,.55);
}

.catalog-heading {
  margin: 4px 0 10px;
}

.catalog-heading p {
  margin: 0;
}

.catalog-card {
  min-height: 360px;
  opacity: .88;
  background: rgba(10,25,42,.84);
}

.catalog-card:hover {
  opacity: 1;
}

.catalog-card .status-pill {
  font-size: 11px;
}

.catalog-actions {
  grid-template-columns: 1fr 1fr !important;
}

@media (max-width: 1100px) {
  .operational-summary {
    grid-template-columns: repeat(3, minmax(0,1fr));
  }
  .runtime-focus-kpis {
    grid-template-columns: repeat(2, minmax(0,1fr));
  }
}

@media (max-width: 700px) {
  .operational-summary {
    grid-template-columns: repeat(2, minmax(0,1fr));
  }
  .runtime-focus-heading,
  .section-heading {
    flex-direction: column;
  }
  .runtime-focus-kpis {
    grid-template-columns: 1fr;
  }
  .runtime-focus-actions {
    display: grid;
    grid-template-columns: 1fr;
  }
  .runtime-focus-actions button {
    width: 100%;
  }
}
'''
css.write_text(c)
