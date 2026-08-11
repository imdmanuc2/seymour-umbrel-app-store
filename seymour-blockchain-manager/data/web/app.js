const state = {
  providers: [],
  telemetry: {},
  family: "all",
  query: "",
  runtimePresentation: {},
};

const RUNTIME_PRESENTATION_GRACE_MS = 20000;

const grid = document.getElementById("providerGrid");
const filters = document.getElementById("filters");
const search = document.getElementById("search");
const dialog = document.getElementById("providerDialog");
const dialogContent = document.getElementById("dialogContent");

function setText(id, value) {
  const node = document.getElementById(id);
  if (node) node.textContent = value;
}

function formatBytes(value) {
  if (value === null || value === undefined) return "—";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let size = Number(value);
  let index = 0;
  while (size >= 1000 && index < units.length - 1) {
    size /= 1000;
    index += 1;
  }
  return `${size.toFixed(index > 2 ? 1 : 0)} ${units[index]}`;
}

function providerTelemetry(providerId) {
  return state.telemetry.providers?.[providerId] || null;
}

function rawRuntimeState(provider) {
  const telemetry = providerTelemetry(provider.providerId);
  if (provider.availability !== "live") return "coming-soon";

  return (
    telemetry?.runtimeState ||
    telemetry?.operationalState?.state ||
    telemetry?.runtime?.runtimeState ||
    telemetry?.lifecycleStatus ||
    "unknown"
  );
}

function hasCompleteSyncTelemetry(telemetry) {
  const sync = telemetry?.sync || {};
  return (
    Number.isFinite(Number(sync.progressPercent)) &&
    Number.isFinite(Number(sync.height)) &&
    Number.isFinite(Number(sync.headers))
  );
}

function presentedRuntime(provider) {
  const providerId = provider.providerId;
  const telemetry = providerTelemetry(providerId);
  const rawState = rawRuntimeState(provider);
  const now = Date.now();

  if (provider.availability !== "live") {
    return {state: rawState, telemetry, graceHeld: false};
  }

  const current = state.runtimePresentation[providerId] || null;
  const isGoodLiveState = ["running", "syncing", "starting"].includes(rawState);
  const completeSyncTelemetry =
    rawState !== "syncing" || hasCompleteSyncTelemetry(telemetry);

  if (isGoodLiveState && completeSyncTelemetry) {
    state.runtimePresentation[providerId] = {
      state: rawState,
      telemetry,
      lastGoodAt: now,
    };
    return {state: rawState, telemetry, graceHeld: false};
  }

  if (
    rawState === "syncing" &&
    current &&
    current.state === "syncing" &&
    !completeSyncTelemetry &&
    now - current.lastGoodAt <= RUNTIME_PRESENTATION_GRACE_MS
  ) {
    return {
      state: "syncing",
      telemetry: current.telemetry,
      graceHeld: true,
      rawState,
    };
  }

  if (
    current &&
    current.state === "syncing" &&
    ["degraded", "unknown"].includes(rawState) &&
    now - current.lastGoodAt <= RUNTIME_PRESENTATION_GRACE_MS
  ) {
    return {
      state: "syncing",
      telemetry: current.telemetry,
      graceHeld: true,
      rawState,
    };
  }

  return {state: rawState, telemetry, graceHeld: false};
}

function lifecycle(provider) {
  return presentedRuntime(provider).state;
}

function lifecycleLabel(value) {
  return {
    "running": "Running",
    "syncing": "Syncing",
    "starting": "Starting",
    "degraded": "Degraded",
    "stopped": "Stopped",
    "offline": "Offline",
    "error": "Error",
    "not-installed": "Not installed",
    "unknown": "Unknown",
    "coming-soon": "Coming soon",
  }[value] || value;
}

function progressBar(value, label) {
  const normalized = Math.max(0, Math.min(Number(value || 0), 100));
  return `
    <div class="progress-row">
      <div><span>${label}</span><strong>${normalized.toFixed(2)}%</strong></div>
      <div class="progress"><i style="width:${normalized}%"></i></div>
    </div>
  `;
}

function installedProviders() {
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
  const rawProgress = Number(sync.progressPercent);
  const progress = Number.isFinite(rawProgress) ? rawProgress : null;

  const rawHeight = Number(sync.height);
  const rawHeaders = Number(sync.headers);
  const height = Number.isFinite(rawHeight) ? rawHeight : null;
  const headers = Number.isFinite(rawHeaders) ? rawHeaders : null;
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
        presentation.state === "syncing" && progress !== null
          ? `
            <div class="runtime-focus-progress">
              ${progressBar(progress, "Blockchain sync")}
              <div class="runtime-focus-blocks">
                <span>Blocks</span>
                <strong>${
                  height !== null && headers !== null
                    ? `${height.toLocaleString()} / ${headers.toLocaleString()}`
                    : "Telemetry warming up"
                }</strong>
              </div>
            </div>
          `
          : presentation.state === "syncing"
            ? `
              <div class="telemetry-grace-note">
                Sync telemetry is warming up after a runtime transition.
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

function renderHost() {
  const host = state.telemetry.host;
  if (!host) return;

  setText(
    "hostCpu",
    `${Number(host.cpuPercent || 0).toFixed(1)}%`
  );

  setText(
    "hostMemory",
    `${Number(host.memory?.usedPercent || 0).toFixed(1)}%`
  );

  setText(
    "hostStorage",
    formatBytes(host.storage?.freeBytes)
  );

  setText(
    "hostDocker",
    host.docker?.available ? "Online" : "Unavailable"
  );

  setText(
    "hostArchitecture",
    host.architecture || "—"
  );

  document.getElementById("hostPanel")?.classList.toggle(
    "warning",
    !host.healthy
  );
}

function filteredProviders() {
  return state.providers.filter((provider) => {
    const familyMatch =
      state.family === "all" ||
      provider.family === state.family;
    const haystack = [
      provider.displayName,
      provider.ticker,
      provider.implementation,
      provider.miningAlgorithm,
      provider.family,
    ].join(" ").toLowerCase();
    return familyMatch &&
      haystack.includes(state.query.toLowerCase());
  });
}


function renderFilters() {
  const families = [
    "all",
    ...new Set(
      state.providers.map((item) => item.family)
    ),
  ];

  filters.innerHTML = families.map((family) => `
    <button
      class="${family === state.family ? "active" : ""}"
      data-family="${family}"
    >
      ${family === "all" ? "All" : family}
    </button>
  `).join("");

  filters.querySelectorAll("[data-family]").forEach((button) => {
    button.addEventListener("click", () => {
      state.family = button.dataset.family;
      renderFilters();
      renderProviders();
    });
  });
}

function liveMetrics(provider) {
  const presentation = presentedRuntime(provider);
  const telemetry = presentation.telemetry;
  if (!telemetry) return "";

  const sync = telemetry.sync || {};
  const progress = sync.progressPercent;
  const peerValue = telemetry.peers ?? "—";
  const mempoolValue =
    typeof telemetry.mempool === "number"
      ? formatBytes(telemetry.mempool)
      : telemetry.mempool ?? "—";

  const height = sync.height ?? "—";
  const headers = sync.headers ?? "—";
  const blockContext =
    sync.height !== null && sync.height !== undefined &&
    sync.headers !== null && sync.headers !== undefined
      ? `${Number(sync.height).toLocaleString()} / ${Number(sync.headers).toLocaleString()}`
      : "—";

  const rpcHealthy =
    telemetry.runtimeRpcHealthy ??
    telemetry.rpc?.healthy ??
    telemetry.rpc?.reachable ??
    false;

  return `
    ${
      progress !== null && progress !== undefined
        ? `
          <div class="sync-progress-block">
            ${progressBar(progress, "Sync progress")}
            <div class="sync-context">
              <span>Blocks</span>
              <strong>${blockContext}</strong>
            </div>
          </div>
        `
        : ""
    }
    ${
      presentation.graceHeld
        ? `
          <div class="telemetry-grace-note">
            Live telemetry reconnecting · showing last confirmed sync state
          </div>
        `
        : ""
    }
    <dl class="metadata live-metadata">
      <div><dt>Height</dt><dd>${height}</dd></div>
      <div><dt>Headers</dt><dd>${headers}</dd></div>
      <div><dt>Peers</dt><dd>${peerValue}</dd></div>
      <div><dt>Mempool</dt><dd>${mempoolValue}</dd></div>
      <div><dt>Chain data</dt><dd>${formatBytes(telemetry.data?.usedBytes)}</dd></div>
      <div><dt>RPC</dt><dd class="${rpcHealthy ? "metric-good" : "metric-bad"}">${rpcHealthy ? "Healthy" : "Unavailable"}</dd></div>
    </dl>
  `;
}

function renderProviders() {
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

function showDetails(providerId) {
  const provider = state.providers.find(
    (item) => item.providerId === providerId
  );
  const telemetry = providerTelemetry(providerId);
  const ports = Object.entries(provider.defaultPorts)
    .map(([name, port]) => `<li><strong>${name}</strong>: ${port}</li>`)
    .join("");

  dialogContent.innerHTML = `
    <p class="provider-family">${provider.family}</p>
    <h2>${provider.displayName} <span>${provider.ticker}</span></h2>
    <p>${provider.implementation} ${provider.nodeVersion}</p>
    <dl class="dialog-metadata">
      <div><dt>Status</dt><dd>${lifecycleLabel(lifecycle(provider))}</dd></div>
      <div><dt>Network</dt><dd>${provider.network}</dd></div>
      <div><dt>Mining</dt><dd>${provider.miningAlgorithm}</dd></div>
      <div><dt>Disk estimate</dt><dd>${formatBytes(provider.estimatedDiskBytes)}</dd></div>
      <div><dt>Installed data</dt><dd>${formatBytes(telemetry?.data?.usedBytes)}</dd></div>
    </dl>
    <h3>Default ports</h3>
    <ul>${ports}</ul>
  `;

  dialog.showModal();
}

function showManage(providerId) {
  const provider = state.providers.find(
    (item) => item.providerId === providerId
  );
  const presentation = presentedRuntime(provider);
  const telemetry = presentation.telemetry || {};
  const runtimeState = presentation.state;
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

async function loadCatalog() {
  const response = await fetch("/api/providers", {cache: "no-store"});
  if (!response.ok) throw new Error(`Catalog ${response.status}`);
  const payload = await response.json();
  state.providers = payload.providers;
  setText(
    "catalogStatus",
    `Catalog ${payload.catalogVersion} · Live telemetry`
  );

  renderFilters();
}

async function refreshTelemetry() {
  try {
    const response = await fetch("/api/dashboard", {cache: "no-store"});
    if (!response.ok) throw new Error(`Dashboard ${response.status}`);
    state.telemetry = await response.json();
    renderHost();
    renderOperationalSummary();
    renderRuntimeFocus();
    renderProviders();
  } catch (error) {
    setText(
      "catalogStatus",
      `Telemetry error: ${error.message}`
    );
  }
}

search.addEventListener("input", () => {
  state.query = search.value;
  renderProviders();
});

document.getElementById("closeDialog").addEventListener(
  "click",
  () => dialog.close()
);

dialog.addEventListener("click", (event) => {
  if (event.target === dialog) dialog.close();
});

async function boot() {
  await loadCatalog();
  await refreshTelemetry();
  setInterval(refreshTelemetry, 5000);
}

boot().catch((error) => {
  grid.innerHTML = `<p class="error">${error.message}</p>`;
});

async function openInstallWizard(providerId) {
  const provider = state.providers.find((item) => item.providerId === providerId);
  const preflight = await (await fetch("/api/install/preflight", {cache: "no-store"})).json();
  const credentials = await (await fetch("/api/install/credentials", {cache: "no-store"})).json();
  dialogContent.innerHTML = `<p class="provider-family">installation wizard</p><h2>${provider.displayName}</h2><ol class="wizard-steps"><li class="active">Validate</li><li>Configure</li><li>Review</li><li>Install</li><li>Verify</li></ol><section class="wizard-section"><pre>${JSON.stringify(preflight,null,2)}</pre></section><section class="wizard-section"><label>Node name<input id="wizardNodeName" value="Seymour Bitcoin Cash Node"></label><label>RPC user<input id="wizardRpcUser" value="${credentials.rpcUser}"></label><label>RPC password<input id="wizardRpcPassword" type="password" value="${credentials.rpcPassword}"></label><label>RPC port<input id="wizardRpcPort" type="number" value="${provider.defaultPorts.rpc}"></label><label>P2P port<input id="wizardP2pPort" type="number" value="${provider.defaultPorts.p2p}"></label></section><button id="wizardInstall" class="primary wizard-install" ${preflight.compatible ? "" : "disabled"}>Install Bitcoin Cash</button><pre id="wizardResult" class="operation-result"></pre>`;
  document.getElementById("wizardInstall")?.addEventListener("click", async () => {
    if (!confirm(`Install ${provider.displayName}?\n\n${provider.installAction.confirmation}`)) return;
    const response = await fetch("/api/install/execute", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({providerId:provider.providerId,appId:provider.installAction.appId,nodeName:document.getElementById("wizardNodeName").value,rpcUser:document.getElementById("wizardRpcUser").value,rpcPassword:document.getElementById("wizardRpcPassword").value,rpcPort:Number(document.getElementById("wizardRpcPort").value),p2pPort:Number(document.getElementById("wizardP2pPort").value),confirmation:provider.installAction.confirmation})});
    document.getElementById("wizardResult").textContent = JSON.stringify(await response.json(), null, 2);
    await refreshTelemetry();
  });
  dialog.showModal();
}
function formatDuration(seconds) {
  if (seconds === null || seconds === undefined) return "Calculating…";
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h ${minutes % 60}m`;
}

async function showSyncManager(providerId) {
  const provider = state.providers.find((item) => item.providerId === providerId);
  const response = await fetch("/api/sync", {cache: "no-store"});
  const sync = await response.json();
  const recommendations = sync.recommendations.map((item) => `
    <li class="recommendation ${item.severity}">
      <strong>${item.code}</strong><span>${item.message}</span>
    </li>`).join("");
  dialogContent.innerHTML = `
    <p class="provider-family">initial sync manager</p>
    <h2>${provider.displayName}</h2>
    <div class="sync-kpis">
      <article><span>Progress</span><strong>${sync.snapshot.progress_percent ?? "—"}%</strong></article>
      <article><span>Blocks remaining</span><strong>${sync.blocksRemaining ?? "—"}</strong></article>
      <article><span>Rate</span><strong>${sync.blocksPerSecond ?? "—"} blk/s</strong></article>
      <article><span>ETA</span><strong>${formatDuration(sync.etaSeconds)}</strong></article>
    </div>
    <dl class="dialog-metadata">
      <div><dt>Height</dt><dd>${sync.snapshot.height ?? "—"}</dd></div>
      <div><dt>Headers</dt><dd>${sync.snapshot.headers ?? "—"}</dd></div>
      <div><dt>Peers</dt><dd>${sync.snapshot.peers ?? "—"}</dd></div>
      <div><dt>Peer quality</dt><dd>${sync.peerQuality.state}</dd></div>
      <div><dt>Stalled</dt><dd>${sync.stall.stalled ? "Yes" : "No"}</dd></div>
    </dl>
    <h3>Recommendations</h3>
    <ul class="recommendations">${recommendations}</ul>`;
  dialog.showModal();
}

async function fetchJsonWithTimeout(
  url,
  options = {},
  timeoutMs = 12000
) {
  const controller = new AbortController();
  const timer = window.setTimeout(
    () => controller.abort(),
    timeoutMs
  );

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });

    let payload = null;
    try {
      payload = await response.json();
    } catch {
      payload = {
        error: "invalid-json-response",
        message: `HTTP ${response.status}`,
      };
    }

    return {
      ok: response.ok,
      status: response.status,
      payload,
      timedOut: false,
    };
  } catch (error) {
    if (error?.name === "AbortError") {
      return {
        ok: false,
        status: 0,
        payload: {
          error: "request-timeout",
          message: `Request exceeded ${Math.round(timeoutMs / 1000)} seconds.`,
        },
        timedOut: true,
      };
    }

    return {
      ok: false,
      status: 0,
      payload: {
        error: "network-error",
        message: error?.message || "Network request failed.",
      },
      timedOut: false,
    };
  } finally {
    window.clearTimeout(timer);
  }
}

function evidenceTimestamp(value) {
  if (!value) return "Unknown time";
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime())
    ? value
    : parsed.toLocaleString();
}

function severityClass(value) {
  const severity = String(value || "").toLowerCase();
  if (["error", "critical", "failed"].includes(severity)) {
    return "error";
  }
  if (["warning", "warn", "degraded"].includes(severity)) {
    return "warning";
  }
  if (["success", "healthy", "passed"].includes(severity)) {
    return "success";
  }
  return "info";
}

function renderLifecycleTimeline(target, payload) {
  if (!target) return;

  const items = Array.isArray(payload?.items)
    ? payload.items
    : [];

  if (!items.length) {
    target.innerHTML = `
      <div class="ops-empty-state">
        No lifecycle evidence recorded yet.
      </div>
    `;
    return;
  }

  target.innerHTML = `
    <div class="ops-timeline">
      ${items.map((item) => `
        <article class="ops-timeline-item ${severityClass(item.severity)}">
          <div class="ops-timeline-marker"></div>
          <div class="ops-timeline-content">
            <div class="ops-timeline-top">
              <strong>${item.eventType || "Lifecycle event"}</strong>
              <time>${evidenceTimestamp(item.recordedAt || item.observedAt)}</time>
            </div>
            <p>${item.message || item.reason || "Lifecycle evidence recorded."}</p>
            <div class="ops-timeline-meta">
              ${item.action ? `<span>${item.action}</span>` : ""}
              ${item.lifecycleState ? `<span>${lifecycleLabel(item.lifecycleState)}</span>` : ""}
              ${item.auditId ? `<span>Audit ${item.auditId}</span>` : ""}
            </div>
          </div>
        </article>
      `).join("")}
    </div>
  `;
}

function flattenDiagnosticEntries(payload) {
  if (!payload || typeof payload !== "object") return [];

  const candidates = [
    payload.checks,
    payload.results,
    payload.diagnostics,
    payload.items,
  ].find(Array.isArray);

  if (candidates) {
    return candidates.map((item, index) => ({
      name:
        item.name ||
        item.check ||
        item.title ||
        `Check ${index + 1}`,
      status:
        item.status ||
        (item.success === true
          ? "passed"
          : item.success === false
            ? "failed"
            : "info"),
      message:
        item.message ||
        item.detail ||
        item.reason ||
        "",
    }));
  }

  return Object.entries(payload)
    .filter(([, value]) => (
      typeof value === "string" ||
      typeof value === "number" ||
      typeof value === "boolean"
    ))
    .slice(0, 12)
    .map(([name, value]) => ({
      name,
      status: "info",
      message: String(value),
    }));
}

function renderDiagnostics(target, payload) {
  if (!target) return;

  const entries = flattenDiagnosticEntries(payload);

  if (!entries.length) {
    target.innerHTML = `
      <div class="ops-empty-state">
        Diagnostics returned no structured checks. Raw evidence is shown below.
      </div>
    `;
    return;
  }

  target.innerHTML = `
    <div class="ops-diagnostic-grid">
      ${entries.map((item) => `
        <article class="ops-diagnostic-card ${severityClass(item.status)}">
          <span>${item.status}</span>
          <strong>${item.name}</strong>
          ${item.message ? `<p>${item.message}</p>` : ""}
        </article>
      `).join("")}
    </div>
  `;
}

function extractLogs(payload) {
  if (typeof payload === "string") return payload;

  for (const key of ["logs", "lines", "output", "stdout"]) {
    const value = payload?.[key];
    if (typeof value === "string") return value;
    if (Array.isArray(value)) return value.join("\n");
  }

  return JSON.stringify(payload, null, 2);
}

function renderLogs(target, payload) {
  if (!target) return;
  target.textContent = extractLogs(payload);
  target.scrollTop = target.scrollHeight;
}

async function lifecycleRequest(provider, action, execute = false, confirmation = null) {
  const appId = provider.installAction?.appId;
  if (!appId) {
    throw new Error("Provider has no lifecycle appId");
  }

  const body = {
    appId,
    action,
    execute,
  };

  if (confirmation) {
    body.confirmation = confirmation;
  }

  return fetchJsonWithTimeout(
    "/api/lifecycle/operation",
    {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(body),
    },
    30000
  );
}

async function lifecyclePlan(provider, action) {
  return lifecycleRequest(provider, action, false, null);
}

async function lifecycleExecute(provider, action, confirmation) {
  return lifecycleRequest(
    provider,
    action,
    true,
    confirmation
  );
}

function allowedLifecycleActions(runtimeState) {
  const policy = {
    running: ["restart", "stop"],
    syncing: ["restart", "stop"],
    degraded: ["restart", "stop"],
    starting: ["stop"],
    stopped: ["start"],
    offline: ["start"],
    error: ["restart"],
    unknown: [],
  };

  return new Set(policy[runtimeState] || []);
}

function lifecycleActionLabel(action) {
  return {
    start: "Start",
    stop: "Stop",
    restart: "Restart",
  }[action] || action;
}

function operationStatusClass(payload) {
  if (!payload) return "neutral";
  if (payload.success === true || payload.eventType === "lifecycle.action.planned") {
    return "success";
  }
  if (payload.allowed === false || payload.success === false) {
    return "warning";
  }
  return "neutral";
}

function renderOperationResult(target, payload, title = "Result") {
  if (!target) return;

  const status = operationStatusClass(payload);
  const reason =
    payload?.reason ||
    payload?.message ||
    payload?.error ||
    "Operation response received.";

  target.innerHTML = `
    <div class="ops-result-card ${status}">
      <div class="ops-result-heading">
        <strong>${title}</strong>
        ${
          payload?.lifecycleState
            ? `<span class="status-pill">${lifecycleLabel(payload.lifecycleState)}</span>`
            : ""
        }
      </div>
      <p>${reason}</p>
      ${
        payload?.confirmationToken
          ? `<code>${payload.confirmationToken}</code>`
          : ""
      }
      ${
        payload?.auditId
          ? `<small>Audit ${payload.auditId}</small>`
          : ""
      }
    </div>
  `;
}

async function showOperationsCenter(providerId) {
  const provider = state.providers.find(
    (item) => item.providerId === providerId
  );
  const presentation = presentedRuntime(provider);
  const telemetry = presentation.telemetry || {};
  const sync = telemetry.sync || {};
  const runtimeState = presentation.state;
  const allowed = allowedLifecycleActions(runtimeState);

  const rpcHealthy =
    telemetry.runtimeRpcHealthy ??
    telemetry.rpc?.healthy ??
    telemetry.rpc?.reachable ??
    false;

  const progress =
    sync.progressPercent !== null && sync.progressPercent !== undefined
      ? `${Number(sync.progressPercent).toFixed(2)}%`
      : "—";

  dialogContent.innerHTML = `
    <div class="ops-shell">
      <div class="ops-header">
        <div>
          <p class="provider-family">operations center</p>
          <h2>${provider.displayName}</h2>
          <p class="implementation">
            Canonical guarded operations for ${provider.installAction?.appId || "managed runtime"}.
          </p>
        </div>
        <span class="status-pill ${runtimeState}">
          ${lifecycleLabel(runtimeState)}
        </span>
      </div>

      <section class="ops-runtime-strip">
        <article>
          <span>Runtime</span>
          <strong>${lifecycleLabel(runtimeState)}</strong>
        </article>
        <article>
          <span>RPC</span>
          <strong class="${rpcHealthy ? "metric-good" : "metric-bad"}">
            ${rpcHealthy ? "Healthy" : "Unavailable"}
          </strong>
        </article>
        <article>
          <span>Peers</span>
          <strong>${telemetry.peers ?? "—"}</strong>
        </article>
        <article>
          <span>Sync</span>
          <strong>${progress}</strong>
        </article>
      </section>

      <section class="ops-section">
        <div class="ops-section-heading">
          <div>
            <p class="eyebrow">Diagnostics</p>
            <h3>Observe before changing</h3>
          </div>
        </div>
        <div class="ops-action-grid">
          <button id="opsDiagnostics" class="secondary">Run diagnostics</button>
          <button id="opsLogs" class="secondary">View recent logs</button>
          <button id="opsHistory" class="secondary">Lifecycle history</button>
        </div>
      </section>

      <section class="ops-section">
        <div class="ops-section-heading">
          <div>
            <p class="eyebrow">Lifecycle</p>
            <h3>Guarded runtime control</h3>
          </div>
          <span class="ops-safety-note">Plan → confirm → execute</span>
        </div>

        <div class="ops-action-grid lifecycle-control-grid">
          <button
            id="opsStart"
            class="secondary"
            ${allowed.has("start") ? "" : "disabled"}
          >Start</button>
          <button
            id="opsRestart"
            class="secondary"
            ${allowed.has("restart") ? "" : "disabled"}
          >Restart</button>
          <button
            id="opsStop"
            class="danger"
            ${allowed.has("stop") ? "" : "disabled"}
          >Stop</button>
        </div>

        <div id="opsLifecyclePlan"></div>
      </section>

      <section class="ops-section">
        <div class="ops-section-heading">
          <div>
            <p class="eyebrow">Maintenance</p>
            <h3>Plan controlled change</h3>
          </div>
        </div>

        <div class="ops-action-grid">
          <button id="opsBackupPlan" class="secondary">Plan backup</button>
          <button id="opsRestorePlan" class="secondary">Plan restore</button>
          <button id="opsUpgradePlan" class="secondary">Plan upgrade</button>
        </div>

        <div id="opsMaintenanceExecute"></div>
      </section>

      <section class="ops-section ops-evidence-view">
        <div class="ops-section-heading">
          <div>
            <p class="eyebrow">Lifecycle timeline</p>
            <h3>Recent guarded operations</h3>
          </div>
          <button id="opsRefreshHistory" class="ops-link-button">Refresh</button>
        </div>
        <div id="opsHistoryView" class="ops-history-view">
          <div class="ops-empty-state">Load lifecycle history to view evidence.</div>
        </div>
      </section>

      <section class="ops-section ops-evidence-view">
        <div class="ops-section-heading">
          <div>
            <p class="eyebrow">Diagnostics</p>
            <h3>Health checks</h3>
          </div>
        </div>
        <div id="opsDiagnosticsView">
          <div class="ops-empty-state">Run diagnostics to populate health checks.</div>
        </div>
      </section>

      <section class="ops-section ops-evidence-view">
        <div class="ops-section-heading">
          <div>
            <p class="eyebrow">Logs</p>
            <h3>Recent runtime logs</h3>
          </div>
        </div>
        <pre id="opsLogsView" class="ops-log-view">Open recent logs to populate this viewer.</pre>
      </section>

      <section class="ops-output-section">
        <div class="ops-section-heading">
          <div>
            <p class="eyebrow">Raw evidence</p>
            <h3>Operation output</h3>
          </div>
          <button id="opsClearOutput" class="ops-link-button">Clear</button>
        </div>
        <pre id="opsResult" class="operation-result ops-result-output">No operation selected.</pre>
      </section>
    </div>
  `;

  const output = document.getElementById("opsResult");
  const lifecyclePlanTarget = document.getElementById("opsLifecyclePlan");
  const maintenanceExecute = document.getElementById("opsMaintenanceExecute");
  const historyView = document.getElementById("opsHistoryView");
  const diagnosticsView = document.getElementById("opsDiagnosticsView");
  const logsView = document.getElementById("opsLogsView");

  const writeOutput = (payload) => {
    output.textContent = JSON.stringify(payload, null, 2);
  };

  document.getElementById("opsClearOutput")?.addEventListener(
    "click",
    () => {
      output.textContent = "No operation selected.";
      lifecyclePlanTarget.innerHTML = "";
      maintenanceExecute.innerHTML = "";
    }
  );

  document.getElementById("opsDiagnostics")?.addEventListener(
    "click",
    async () => {
      output.textContent = "Running diagnostics…";
      diagnosticsView.innerHTML =
        `<div class="ops-inline-loading">Running diagnostics…</div>`;

      const result = await fetchJsonWithTimeout(
        "/api/operations/diagnostics",
        {cache: "no-store"},
        15000
      );

      writeOutput(result.payload);
      renderDiagnostics(diagnosticsView, result.payload);

      if (!result.ok) {
        renderOperationResult(
          diagnosticsView,
          result.payload,
          result.timedOut ? "Diagnostics timeout" : "Diagnostics unavailable"
        );
      }
    }
  );

  document.getElementById("opsLogs")?.addEventListener(
    "click",
    async () => {
      output.textContent = "Loading recent logs…";
      logsView.textContent = "Loading recent logs…";

      const result = await fetchJsonWithTimeout(
        "/api/operations/logs",
        {cache: "no-store"},
        12000
      );

      writeOutput(result.payload);
      renderLogs(logsView, result.payload);
    }
  );

  async function loadLifecycleHistory() {
    historyView.innerHTML =
      `<div class="ops-inline-loading">Loading lifecycle history…</div>`;

    const appId = encodeURIComponent(
      provider.installAction?.appId || ""
    );

    const result = await fetchJsonWithTimeout(
      `/api/lifecycle/history?appId=${appId}`,
      {cache: "no-store"},
      12000
    );

    writeOutput(result.payload);

    if (result.ok) {
      renderLifecycleTimeline(historyView, result.payload);
    } else {
      renderOperationResult(
        historyView,
        result.payload,
        result.timedOut ? "History timeout" : "History unavailable"
      );
    }
  }

  document.getElementById("opsHistory")?.addEventListener(
    "click",
    loadLifecycleHistory
  );

  document.getElementById("opsRefreshHistory")?.addEventListener(
    "click",
    loadLifecycleHistory
  );

  async function planLifecycle(action) {
    lifecyclePlanTarget.innerHTML =
      `<div class="ops-inline-loading">Planning ${action}…</div>`;

    const result = await lifecyclePlan(provider, action);
    const payload = result.payload;

    renderOperationResult(
      lifecyclePlanTarget,
      payload,
      result.timedOut
        ? `${lifecycleActionLabel(action)} plan timeout`
        : `${lifecycleActionLabel(action)} plan`
    );

    writeOutput(payload);

    if (!result.ok || payload?.allowed !== true) {
      return;
    }

    await loadLifecycleHistory();

    const token = payload.confirmationToken;
    if (!token) {
      return;
    }

    const executeButton = document.createElement("button");
    executeButton.className =
      action === "stop"
        ? "danger ops-confirm-execute"
        : "primary ops-confirm-execute";
    executeButton.textContent =
      `Execute ${lifecycleActionLabel(action)}`;

    lifecyclePlanTarget.appendChild(executeButton);

    executeButton.addEventListener("click", async () => {
      const confirmed = window.confirm(
        `${lifecycleActionLabel(action)} ${provider.displayName}?\n\n` +
        `Required confirmation:\n${token}`
      );

      if (!confirmed) return;

      executeButton.disabled = true;
      executeButton.textContent =
        `Executing ${lifecycleActionLabel(action)}…`;

      const executeResult = await lifecycleExecute(
        provider,
        action,
        token
      );

      writeOutput(executeResult.payload);
      renderOperationResult(
        lifecyclePlanTarget,
        executeResult.payload,
        `${lifecycleActionLabel(action)} execution`
      );

      await refreshTelemetry();
    });
  }

  document.getElementById("opsStart")?.addEventListener(
    "click",
    () => planLifecycle("start")
  );
  document.getElementById("opsRestart")?.addEventListener(
    "click",
    () => planLifecycle("restart")
  );
  document.getElementById("opsStop")?.addEventListener(
    "click",
    () => planLifecycle("stop")
  );

  async function createMaintenancePlan(kind) {
    maintenanceExecute.innerHTML =
      `<div class="ops-inline-loading">Planning ${kind}…</div>`;

    const result = await fetchJsonWithTimeout(
      "/api/operations/plan",
      {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
          kind,
          details: {providerId},
        }),
      },
      12000
    );

    const payload = result.payload;
    writeOutput(payload);

    renderOperationResult(
      maintenanceExecute,
      payload,
      `${kind[0].toUpperCase()}${kind.slice(1)} plan`
    );

    if (kind !== "backup" || !payload.confirmation) {
      return;
    }

    const executeButton = document.createElement("button");
    executeButton.className = "primary ops-confirm-execute";
    executeButton.textContent = "Execute guarded backup";
    maintenanceExecute.appendChild(executeButton);

    executeButton.addEventListener("click", async () => {
      if (
        !window.confirm(
          `Execute BCH backup?\n\n${payload.confirmation}`
        )
      ) {
        return;
      }

      const executeResponse = await fetch(
        "/api/operations/backup",
        {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({
            confirmation: payload.confirmation,
          }),
        }
      );

      writeOutput(await executeResponse.json());
    });
  }

  document.getElementById("opsBackupPlan")?.addEventListener(
    "click",
    () => createMaintenancePlan("backup")
  );
  document.getElementById("opsRestorePlan")?.addEventListener(
    "click",
    () => createMaintenancePlan("restore")
  );
  document.getElementById("opsUpgradePlan")?.addEventListener(
    "click",
    () => createMaintenancePlan("upgrade")
  );

  dialog.showModal();
  loadLifecycleHistory();
}

async function showAdoptionWizard(providerId) {
  const provider = state.providers.find(
    (item) => item.providerId === providerId
  );

  dialogContent.innerHTML = `
    <p class="provider-family">existing node adoption</p>
    <h2>${provider.displayName}</h2>

    <p>
      Select an existing Bitcoin Cash datadir.
      The Seymour-managed destination must be empty.
    </p>

    <label class="adoption-label">
      Existing datadir path
      <input
        id="adoptionSourcePath"
        placeholder="/path/to/existing/bitcoin-cash-data"
      >
    </label>

    <button id="adoptionPlan" class="secondary">
      Validate and build adoption plan
    </button>

    <div id="adoptionActions"></div>

    <pre
      id="adoptionResult"
      class="operation-result"
    ></pre>
  `;

  document
    .getElementById("adoptionPlan")
    .addEventListener("click", async () => {
      const sourcePath = document.getElementById(
        "adoptionSourcePath"
      ).value;

      const response = await fetch(
        "/api/adoption/plan",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            sourcePath,
          }),
        }
      );

      const plan = await response.json();

      document.getElementById(
        "adoptionResult"
      ).textContent = JSON.stringify(
        plan,
        null,
        2
      );

      if (!plan.validation?.source?.valid) {
        return;
      }

      document.getElementById(
        "adoptionActions"
      ).innerHTML = `
        <button
          id="adoptionExecute"
          class="primary adoption-execute"
        >
          Adopt existing node
        </button>
      `;

      document
        .getElementById("adoptionExecute")
        .addEventListener("click", async () => {
          if (
            !window.confirm(
              `Adopt existing BCH node?\n\n` +
              `${plan.required_confirmation}`
            )
          ) {
            return;
          }

          const executeResponse = await fetch(
            "/api/adoption/execute",
            {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify({
                operationId: plan.operation_id,
                confirmation:
                  plan.required_confirmation,
              }),
            }
          );

          const result =
            await executeResponse.json();

          document.getElementById(
            "adoptionResult"
          ).textContent = JSON.stringify(
            result,
            null,
            2
          );

          await refreshTelemetry();
        });
    });

  dialog.showModal();
}
