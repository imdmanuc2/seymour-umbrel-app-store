from pathlib import Path
import sys

root = Path(sys.argv[1])
js = root / "seymour-blockchain-manager/data/web/app.js"
css = root / "seymour-blockchain-manager/data/web/style.css"

s = js.read_text()

# ---------------------------------------------------------------------------
# Helpers for canonical lifecycle API
# ---------------------------------------------------------------------------
if "async function lifecyclePlan(provider, action)" not in s:
    anchor = "async function showOperationsCenter(providerId) {"
    idx = s.find(anchor)
    if idx < 0:
        raise SystemExit("SBP-043 patch: operations center anchor missing")

    helpers = r'''async function lifecycleRequest(provider, action, execute = false, confirmation = null) {
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

  const response = await fetch("/api/lifecycle/operation", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(body),
  });

  const payload = await response.json();

  return {
    ok: response.ok,
    status: response.status,
    payload,
  };
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

'''
    s = s[:idx] + helpers + s[idx:]

# ---------------------------------------------------------------------------
# Replace Operations Center
# ---------------------------------------------------------------------------
start = s.find("async function showOperationsCenter(providerId) {")
end = s.find("\nasync function showAdoptionWizard", start)
if start < 0 or end < 0:
    raise SystemExit("SBP-043 patch: operations center function boundaries missing")

operations = r'''async function showOperationsCenter(providerId) {
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

      <section class="ops-output-section">
        <div class="ops-section-heading">
          <div>
            <p class="eyebrow">Evidence</p>
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
      const response = await fetch(
        "/api/operations/diagnostics",
        {cache: "no-store"}
      );
      writeOutput(await response.json());
    }
  );

  document.getElementById("opsLogs")?.addEventListener(
    "click",
    async () => {
      output.textContent = "Loading recent logs…";
      const response = await fetch(
        "/api/operations/logs",
        {cache: "no-store"}
      );
      writeOutput(await response.json());
    }
  );

  document.getElementById("opsHistory")?.addEventListener(
    "click",
    async () => {
      output.textContent = "Loading lifecycle history…";
      const appId = encodeURIComponent(
        provider.installAction?.appId || ""
      );
      const response = await fetch(
        `/api/lifecycle/history?appId=${appId}`,
        {cache: "no-store"}
      );
      writeOutput(await response.json());
    }
  );

  async function planLifecycle(action) {
    lifecyclePlanTarget.innerHTML =
      `<div class="ops-inline-loading">Planning ${action}…</div>`;

    const result = await lifecyclePlan(provider, action);
    const payload = result.payload;

    renderOperationResult(
      lifecyclePlanTarget,
      payload,
      `${lifecycleActionLabel(action)} plan`
    );

    writeOutput(payload);

    if (!result.ok || payload.allowed !== true) {
      return;
    }

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

    const response = await fetch(
      "/api/operations/plan",
      {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
          kind,
          details: {providerId},
        }),
      }
    );

    const payload = await response.json();
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
}
'''

s = s[:start] + operations + s[end:]

# Legacy executeLifecycle used /api/lifecycle/<action>; leave install path alone
# but remove the unused function so Operations has one canonical lifecycle route.
legacy_start = s.find("function requiredConfirmation(action, appId) {")
legacy_end = s.find("\nasync function openInstallWizard", legacy_start)
if legacy_start >= 0 and legacy_end >= 0:
    legacy_block = s[legacy_start:legacy_end]
    if "/api/lifecycle/" in legacy_block:
        s = s[:legacy_start] + s[legacy_end:]

js.write_text(s)

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
c = css.read_text()
marker = "/* SBP-043 — live operations experience */"
if marker not in c:
    c += r'''

/* SBP-043 — live operations experience */
#providerDialog:has(.ops-shell) {
  width: min(900px, calc(100% - 30px));
}

.ops-shell {
  display: grid;
  gap: 14px;
}

.ops-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 18px;
  padding-bottom: 4px;
}

.ops-header h2 {
  margin-bottom: 5px;
}

.ops-runtime-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 9px;
}

.ops-runtime-strip article {
  padding: 12px 13px;
  border: 1px solid rgba(83,145,224,.20);
  border-radius: 11px;
  background: rgba(5,17,31,.72);
}

.ops-runtime-strip span {
  display: block;
  margin-bottom: 5px;
  color: var(--muted);
  font-size: 11px;
}

.ops-runtime-strip strong {
  font-size: 15px;
}

.ops-section,
.ops-output-section {
  padding: 15px;
  border: 1px solid rgba(83,145,224,.18);
  border-radius: 13px;
  background: rgba(5,17,31,.55);
}

.ops-section-heading {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 11px;
}

.ops-section-heading h3 {
  margin-bottom: 0;
  font-size: 16px;
}

.ops-safety-note {
  color: #86c1ff;
  font-size: 11px;
}

.ops-action-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0,1fr));
  gap: 8px;
}

.ops-action-grid button,
.ops-confirm-execute,
.ops-link-button {
  min-height: 40px;
  padding: 9px 11px;
  border: 1px solid rgba(83,145,224,.25);
  border-radius: 9px;
  cursor: pointer;
}

.ops-action-grid button:disabled {
  opacity: .38;
  cursor: not-allowed;
}

.ops-confirm-execute {
  width: 100%;
  margin-top: 9px;
}

.ops-result-card {
  margin-top: 10px;
  padding: 12px 13px;
  border: 1px solid rgba(83,145,224,.22);
  border-radius: 10px;
  background: rgba(8,24,40,.85);
}

.ops-result-card.success {
  border-color: rgba(67,217,155,.35);
}

.ops-result-card.warning {
  border-color: rgba(243,155,88,.38);
}

.ops-result-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 7px;
}

.ops-result-card p {
  margin-bottom: 8px;
  color: var(--muted);
  font-size: 12px;
}

.ops-result-card code {
  display: block;
  padding: 8px;
  border-radius: 7px;
  background: rgba(0,0,0,.28);
  color: #9ed0ff;
  font-size: 11px;
  overflow-wrap: anywhere;
}

.ops-result-card small {
  display: block;
  margin-top: 7px;
  color: var(--muted);
}

.ops-inline-loading {
  margin-top: 9px;
  color: var(--muted);
  font-size: 12px;
}

.ops-link-button {
  min-height: auto;
  padding: 5px 8px;
  border-color: transparent;
  background: transparent;
  color: #86c1ff;
}

.ops-result-output {
  min-height: 92px;
  max-height: 260px;
  margin: 0;
}

@media (max-width: 700px) {
  .ops-header,
  .ops-section-heading {
    flex-direction: column;
  }

  .ops-runtime-strip,
  .ops-action-grid {
    grid-template-columns: 1fr;
  }
}
'''
css.write_text(c)
