const state = {
  providers: [],
  telemetry: {},
  family: "all",
  query: "",
};

const grid = document.getElementById("providerGrid");
const filters = document.getElementById("filters");
const search = document.getElementById("search");
const dialog = document.getElementById("providerDialog");
const dialogContent = document.getElementById("dialogContent");

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

function lifecycle(provider) {
  const telemetry = providerTelemetry(provider.providerId);
  if (provider.availability !== "live") return "coming-soon";
  return telemetry?.lifecycleStatus || "unknown";
}

function lifecycleLabel(value) {
  return {
    "running": "Running",
    "syncing": "Syncing",
    "stopped": "Stopped",
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

function renderHost() {
  const host = state.telemetry.host;
  if (!host) return;

  document.getElementById("hostCpu").textContent =
    `${Number(host.cpuPercent || 0).toFixed(1)}%`;

  document.getElementById("hostMemory").textContent =
    `${Number(host.memory?.usedPercent || 0).toFixed(1)}%`;

  document.getElementById("hostStorage").textContent =
    formatBytes(host.storage?.freeBytes);

  document.getElementById("hostDocker").textContent =
    host.docker?.available ? "Online" : "Unavailable";

  document.getElementById("hostArchitecture").textContent =
    host.architecture || "—";

  document.getElementById("hostPanel").classList.toggle(
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
    ...new Set(state.providers.map((item) => item.family)),
  ];

  filters.innerHTML = families.map((family) => `
    <button
      class="${family === state.family ? "active" : ""}"
      data-family="${family}"
    >
      ${family === "all" ? "All" : family}
    </button>
  `).join("");

  filters.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      state.family = button.dataset.family;
      renderFilters();
      renderProviders();
    });
  });
}

function liveMetrics(provider) {
  const telemetry = providerTelemetry(provider.providerId);
  if (!telemetry) return "";

  const sync = telemetry.sync || {};
  const progress = sync.progressPercent;
  const peerValue = telemetry.peers ?? "—";
  const mempoolValue =
    typeof telemetry.mempool === "number"
      ? formatBytes(telemetry.mempool)
      : telemetry.mempool ?? "—";

  return `
    ${progress !== null && progress !== undefined
      ? progressBar(progress, "Sync")
      : ""}

    <dl class="metadata live-metadata">
      <div><dt>Height</dt><dd>${sync.height ?? "—"}</dd></div>
      <div><dt>Headers</dt><dd>${sync.headers ?? "—"}</dd></div>
      <div><dt>Peers</dt><dd>${peerValue}</dd></div>
      <div><dt>Mempool</dt><dd>${mempoolValue}</dd></div>
      <div><dt>Chain data</dt><dd>${formatBytes(telemetry.data?.usedBytes)}</dd></div>
      <div><dt>RPC</dt><dd>${telemetry.rpc?.reachable ? "Healthy" : "Unavailable"}</dd></div>
    </dl>
  `;
}

function renderProviders() {
  const providers = filteredProviders();

  grid.innerHTML = providers.map((provider) => {
    const status = lifecycle(provider);
    return `
      <article class="provider-card ${provider.availability} ${status}">
        <div class="card-top">
          <div class="coin-badge">${provider.ticker}</div>
          <span class="status-pill">${lifecycleLabel(status)}</span>
        </div>

        <div>
          <p class="provider-family">${provider.family}</p>
          <h2>${provider.displayName}</h2>
          <p class="implementation">
            ${provider.implementation} ${provider.nodeVersion}
          </p>
        </div>

        ${provider.availability === "live"
          ? liveMetrics(provider)
          : `
            <dl class="metadata">
              <div><dt>Mining</dt><dd>${provider.miningAlgorithm}</dd></div>
              <div><dt>Disk estimate</dt><dd>${formatBytes(provider.estimatedDiskBytes)}</dd></div>
              <div><dt>Architecture</dt><dd>${provider.supportedArchitectures.join(" · ")}</dd></div>
            </dl>
          `
        }

        <div class="card-actions">
          <button class="secondary" data-details="${provider.providerId}">
            View details
          </button>
          ${provider.selectable
            ? `<button class="primary" data-manage="${provider.providerId}">Manage</button>`
            : `<button class="disabled" disabled>Coming soon</button>`
          }
        </div>
      </article>
    `;
  }).join("");

  grid.querySelectorAll("[data-details]").forEach((button) => {
    button.addEventListener("click", () => {
      showDetails(button.dataset.details);
    });
  });

  grid.querySelectorAll("[data-manage]").forEach((button) => {
    button.addEventListener("click", () => {
      showManage(button.dataset.manage);
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
  const telemetry = providerTelemetry(providerId);

  dialogContent.innerHTML = `
    <p class="provider-family">management</p>
    <h2>${provider.displayName}</h2>
    <p>
      Current state:
      <strong>${lifecycleLabel(lifecycle(provider))}</strong>
    </p>
    <div class="install-contract">
      <code>App ID: ${provider.installAction?.appId || "—"}</code>
      <code>Image: ${provider.productionImage || "—"}</code>
      <code>RPC: ${telemetry?.rpc?.reachable ? "Healthy" : "Unavailable"}</code>
    </div>
    <p>
      Lifecycle buttons will be enabled by the next guarded operations package.
    </p>
  `;

  dialog.showModal();
}

async function loadCatalog() {
  const response = await fetch("/api/providers", {cache: "no-store"});
  if (!response.ok) throw new Error(`Catalog ${response.status}`);
  const payload = await response.json();
  state.providers = payload.providers;

  const live = state.providers.filter(
    (provider) => provider.availability === "live"
  ).length;

  document.getElementById("providerCount").textContent =
    payload.providerCount;
  document.getElementById("liveCount").textContent = live;
  document.getElementById("plannedCount").textContent =
    payload.providerCount - live;
  document.getElementById("catalogStatus").textContent =
    `Catalog ${payload.catalogVersion} · Live telemetry`;

  renderFilters();
}

async function refreshTelemetry() {
  try {
    const response = await fetch("/api/dashboard", {cache: "no-store"});
    if (!response.ok) throw new Error(`Dashboard ${response.status}`);
    state.telemetry = await response.json();
    renderHost();
    renderProviders();
  } catch (error) {
    document.getElementById("catalogStatus").textContent =
      `Telemetry error: ${error.message}`;
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
