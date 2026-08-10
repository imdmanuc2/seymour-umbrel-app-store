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

  if (isGoodLiveState) {
    state.runtimePresentation[providerId] = {
      state: rawState,
      telemetry,
      lastGoodAt: now,
    };
    return {state: rawState, telemetry, graceHeld: false};
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

        ${
          provider.availability === "live"
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
        </div>
      </article>
    `;
  }).join("");

  grid.querySelectorAll("[data-details]").forEach((button) => {
    button.addEventListener("click", () => {
      showDetails(button.dataset.details);
    });
  });

  grid.querySelectorAll("[data-sync]").forEach((button) => {
    button.addEventListener("click", () => {
      showSyncManager(button.dataset.sync);
    });
  });

  grid.querySelectorAll("[data-adopt]").forEach((button) => {
    button.addEventListener("click", () => {
      showAdoptionWizard(button.dataset.adopt);
    });
  });

  grid.querySelectorAll("[data-operations]").forEach((button) => {
    button.addEventListener("click", () => {
      showOperationsCenter(button.dataset.operations);
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
function requiredConfirmation(action, appId) {
  return action === "state" ? null : `${action.toUpperCase()}-${appId}`;
}

async function executeLifecycle(provider, action) {
  const appId = provider.installAction.appId;
  const confirmation = requiredConfirmation(action, appId);
  if (confirmation && !window.confirm(`${action.toUpperCase()} ${provider.displayName}?\n\n${confirmation}`)) return;
  const response = await fetch(`/api/lifecycle/${action}`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({providerId: provider.providerId, appId, confirmation}),
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || "Lifecycle operation failed");
  await refreshTelemetry();
  return payload;
}
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

async function showOperationsCenter(providerId) {
  dialogContent.innerHTML = `<p class="provider-family">operations center</p><h2>Bitcoin Cash</h2><div class="operations-actions"><button id="opsDiagnostics" class="secondary">Run diagnostics</button><button id="opsLogs" class="secondary">View logs</button><button id="opsBackupPlan" class="secondary">Plan backup</button><button id="opsRestorePlan" class="secondary">Plan restore</button><button id="opsUpgradePlan" class="secondary">Plan upgrade</button></div><div id="opsExecute"></div><pre id="opsResult" class="operation-result"></pre>`;
  const output=document.getElementById("opsResult"); const execute=document.getElementById("opsExecute");
  document.getElementById("opsDiagnostics").onclick=async()=>{output.textContent=JSON.stringify(await (await fetch("/api/operations/diagnostics")).json(),null,2)};
  document.getElementById("opsLogs").onclick=async()=>{output.textContent=JSON.stringify(await (await fetch("/api/operations/logs")).json(),null,2)};
  async function createPlan(kind){const payload=await (await fetch("/api/operations/plan",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({kind,details:{providerId}})})).json();output.textContent=JSON.stringify(payload,null,2);if(kind==="backup"){execute.innerHTML='<button id="opsBackupExecute" class="primary operations-execute">Execute guarded backup</button>';document.getElementById("opsBackupExecute").onclick=async()=>{if(!confirm(`Execute BCH backup?\n\n${payload.confirmation}`))return;output.textContent=JSON.stringify(await (await fetch("/api/operations/backup",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({confirmation:payload.confirmation})})).json(),null,2)}}}
  document.getElementById("opsBackupPlan").onclick=()=>createPlan("backup");document.getElementById("opsRestorePlan").onclick=()=>createPlan("restore");document.getElementById("opsUpgradePlan").onclick=()=>createPlan("upgrade");dialog.showModal();
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
