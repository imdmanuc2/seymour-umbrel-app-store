from pathlib import Path
import sys

root = Path(sys.argv[1])
js = root / "seymour-blockchain-manager/data/web/app.js"
css = root / "seymour-blockchain-manager/data/web/style.css"

s = js.read_text()

# ---------------------------------------------------------------------------
# Shared resilient fetch helper
# ---------------------------------------------------------------------------
if "async function fetchJsonWithTimeout(" not in s:
    anchor = "async function lifecycleRequest(provider, action, execute = false, confirmation = null) {"
    idx = s.find(anchor)
    if idx < 0:
        raise SystemExit("SBP-044 patch: lifecycleRequest anchor missing")

    helper = r'''async function fetchJsonWithTimeout(
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

'''
    s = s[:idx] + helper + s[idx:]

# Replace lifecycleRequest's raw fetch with resilient fetch.
start = s.find("async function lifecycleRequest(provider, action, execute = false, confirmation = null) {")
end = s.find("\nasync function lifecyclePlan", start)
if start < 0 or end < 0:
    raise SystemExit("SBP-044 patch: lifecycleRequest boundaries missing")

block = s[start:end]
old_fetch = '''  const response = await fetch("/api/lifecycle/operation", {
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
'''
new_fetch = '''  return fetchJsonWithTimeout(
    "/api/lifecycle/operation",
    {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(body),
    },
    15000
  );
'''
if old_fetch not in block:
    raise SystemExit("SBP-044 patch: lifecycle fetch block missing")
block = block.replace(old_fetch, new_fetch, 1)
s = s[:start] + block + s[end:]

# ---------------------------------------------------------------------------
# Enhance Operations dialog with structured evidence zones.
# ---------------------------------------------------------------------------
ops_start = s.find("async function showOperationsCenter(providerId) {")
ops_end = s.find("\nasync function showAdoptionWizard", ops_start)
if ops_start < 0 or ops_end < 0:
    raise SystemExit("SBP-044 patch: Operations function boundaries missing")

ops = s[ops_start:ops_end]

# Insert structured evidence sections immediately before raw Evidence output.
old_output = '''      <section class="ops-output-section">
        <div class="ops-section-heading">
          <div>
            <p class="eyebrow">Evidence</p>
            <h3>Operation output</h3>
          </div>
          <button id="opsClearOutput" class="ops-link-button">Clear</button>
        </div>
        <pre id="opsResult" class="operation-result ops-result-output">No operation selected.</pre>
      </section>
'''
new_output = '''      <section class="ops-section ops-evidence-view">
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
'''
if old_output not in ops:
    raise SystemExit("SBP-044 patch: raw Evidence section missing")
ops = ops.replace(old_output, new_output, 1)

# Add element bindings.
old_bind = '''  const output = document.getElementById("opsResult");
  const lifecyclePlanTarget = document.getElementById("opsLifecyclePlan");
  const maintenanceExecute = document.getElementById("opsMaintenanceExecute");
'''
new_bind = '''  const output = document.getElementById("opsResult");
  const lifecyclePlanTarget = document.getElementById("opsLifecyclePlan");
  const maintenanceExecute = document.getElementById("opsMaintenanceExecute");
  const historyView = document.getElementById("opsHistoryView");
  const diagnosticsView = document.getElementById("opsDiagnosticsView");
  const logsView = document.getElementById("opsLogsView");
'''
if old_bind not in ops:
    raise SystemExit("SBP-044 patch: Operations bindings missing")
ops = ops.replace(old_bind, new_bind, 1)

# Replace diagnostics handler.
old_diag = '''  document.getElementById("opsDiagnostics")?.addEventListener(
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
'''
new_diag = '''  document.getElementById("opsDiagnostics")?.addEventListener(
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
'''
if old_diag not in ops:
    raise SystemExit("SBP-044 patch: diagnostics handler missing")
ops = ops.replace(old_diag, new_diag, 1)

# Replace logs handler.
old_logs = '''  document.getElementById("opsLogs")?.addEventListener(
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
'''
new_logs = '''  document.getElementById("opsLogs")?.addEventListener(
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
'''
if old_logs not in ops:
    raise SystemExit("SBP-044 patch: logs handler missing")
ops = ops.replace(old_logs, new_logs, 1)

# Replace history handler with reusable loader.
old_history = '''  document.getElementById("opsHistory")?.addEventListener(
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
'''
new_history = '''  async function loadLifecycleHistory() {
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
'''
if old_history not in ops:
    raise SystemExit("SBP-044 patch: history handler missing")
ops = ops.replace(old_history, new_history, 1)

# Strengthen planLifecycle with timeout/error rendering and history refresh.
old_plan_snippet = '''    const result = await lifecyclePlan(provider, action);
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
'''
new_plan_snippet = '''    const result = await lifecyclePlan(provider, action);
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
'''
if old_plan_snippet not in ops:
    raise SystemExit("SBP-044 patch: lifecycle planning block missing")
ops = ops.replace(old_plan_snippet, new_plan_snippet, 1)

# Replace maintenance plan fetch with resilient fetch.
old_maintenance = '''    const response = await fetch(
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
'''
new_maintenance = '''    const result = await fetchJsonWithTimeout(
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
'''
if old_maintenance not in ops:
    raise SystemExit("SBP-044 patch: maintenance planning fetch missing")
ops = ops.replace(old_maintenance, new_maintenance, 1)

# Load lifecycle history once on dialog open.
old_show = '''  dialog.showModal();
}
'''
new_show = '''  dialog.showModal();
  loadLifecycleHistory();
}
'''
if old_show not in ops:
    raise SystemExit("SBP-044 patch: dialog.showModal anchor missing")
ops = ops.replace(old_show, new_show, 1)

s = s[:ops_start] + ops + s[ops_end:]
js.write_text(s)

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
c = css.read_text()
marker = "/* SBP-044 — operations evidence timeline */"
if marker not in c:
    c += r'''

/* SBP-044 — operations evidence timeline */
.ops-evidence-view {
  overflow: hidden;
}

.ops-empty-state {
  padding: 13px 14px;
  border: 1px dashed rgba(83,145,224,.20);
  border-radius: 10px;
  color: var(--muted);
  font-size: 12px;
  background: rgba(5,17,31,.35);
}

.ops-timeline {
  display: grid;
  gap: 0;
}

.ops-timeline-item {
  position: relative;
  display: grid;
  grid-template-columns: 18px 1fr;
  gap: 9px;
  min-height: 66px;
}

.ops-timeline-item:not(:last-child)::before {
  content: "";
  position: absolute;
  left: 6px;
  top: 17px;
  bottom: -2px;
  width: 1px;
  background: rgba(83,145,224,.22);
}

.ops-timeline-marker {
  position: relative;
  z-index: 1;
  width: 13px;
  height: 13px;
  margin-top: 3px;
  border: 3px solid #0c1c2d;
  border-radius: 50%;
  background: #4d9cff;
  box-shadow: 0 0 0 1px rgba(77,156,255,.45);
}

.ops-timeline-item.success .ops-timeline-marker {
  background: #43d99b;
}

.ops-timeline-item.warning .ops-timeline-marker {
  background: #f39b58;
}

.ops-timeline-item.error .ops-timeline-marker {
  background: #ff7777;
}

.ops-timeline-content {
  padding: 0 0 13px;
}

.ops-timeline-top {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}

.ops-timeline-top strong {
  font-size: 12px;
}

.ops-timeline-top time {
  color: var(--muted);
  font-size: 10px;
}

.ops-timeline-content p {
  margin: 4px 0 7px;
  color: var(--muted);
  font-size: 11px;
}

.ops-timeline-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.ops-timeline-meta span {
  padding: 3px 6px;
  border: 1px solid rgba(83,145,224,.16);
  border-radius: 999px;
  color: #9fc3e6;
  font-size: 9px;
}

.ops-diagnostic-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0,1fr));
  gap: 8px;
}

.ops-diagnostic-card {
  min-height: 88px;
  padding: 11px;
  border: 1px solid rgba(83,145,224,.18);
  border-radius: 10px;
  background: rgba(6,20,35,.70);
}

.ops-diagnostic-card > span {
  display: inline-block;
  margin-bottom: 6px;
  color: #86c1ff;
  font-size: 9px;
  text-transform: uppercase;
  letter-spacing: .08em;
}

.ops-diagnostic-card.success {
  border-color: rgba(67,217,155,.28);
}

.ops-diagnostic-card.success > span {
  color: #69e5b2;
}

.ops-diagnostic-card.warning {
  border-color: rgba(243,155,88,.28);
}

.ops-diagnostic-card.warning > span {
  color: #ffb267;
}

.ops-diagnostic-card.error {
  border-color: rgba(255,119,119,.28);
}

.ops-diagnostic-card.error > span {
  color: #ff8c8c;
}

.ops-diagnostic-card strong {
  display: block;
  font-size: 12px;
}

.ops-diagnostic-card p {
  margin-top: 6px;
  color: var(--muted);
  font-size: 10px;
}

.ops-log-view {
  min-height: 150px;
  max-height: 280px;
  margin: 0;
  padding: 12px;
  overflow: auto;
  border: 1px solid rgba(83,145,224,.16);
  border-radius: 9px;
  background: #06111e;
  color: #a8c8e8;
  font: 11px/1.55 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  white-space: pre-wrap;
}

@media (max-width: 700px) {
  .ops-diagnostic-grid {
    grid-template-columns: 1fr;
  }

  .ops-timeline-top {
    flex-direction: column;
  }
}
'''
css.write_text(c)
