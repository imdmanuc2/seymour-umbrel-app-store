from pathlib import Path
import sys

root = Path(sys.argv[1])
js = root / "seymour-blockchain-manager/data/web/app.js"
css = root / "seymour-blockchain-manager/data/web/style.css"

s = js.read_text()

# Extend browser state with presentation-only runtime stabilization memory.
old_state = '''const state = {
  providers: [],
  telemetry: {},
  family: "all",
  query: "",
};
'''
new_state = '''const state = {
  providers: [],
  telemetry: {},
  family: "all",
  query: "",
  runtimePresentation: {},
};

const RUNTIME_PRESENTATION_GRACE_MS = 20000;
'''
if old_state in s:
    s = s.replace(old_state, new_state, 1)
elif "RUNTIME_PRESENTATION_GRACE_MS" not in s:
    raise SystemExit("SBP-041 patch: state anchor not found")

# Insert helpers immediately before lifecycle().
anchor = "function lifecycle(provider) {"
if "function presentedRuntime(provider)" not in s:
    idx = s.find(anchor)
    if idx < 0:
        raise SystemExit("SBP-041 patch: lifecycle anchor missing")
    helper = r'''function rawRuntimeState(provider) {
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

'''
    s = s[:idx] + helper + s[idx:]

# Replace lifecycle with display-state wrapper if necessary.
start = s.find("function lifecycle(provider) {")
end = s.find("\nfunction lifecycleLabel", start)
if start < 0 or end < 0:
    raise SystemExit("SBP-041 patch: lifecycle block missing")
lifecycle_block = '''function lifecycle(provider) {
  return presentedRuntime(provider).state;
}
'''
s = s[:start] + lifecycle_block + s[end:]

# Replace liveMetrics to use the stabilized telemetry snapshot and stronger sync UI.
start = s.find("function liveMetrics(provider) {")
end = s.find("\nfunction renderProviders()", start)
if start < 0 or end < 0:
    raise SystemExit("SBP-041 patch: liveMetrics anchors missing")

live_metrics = r'''function liveMetrics(provider) {
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
'''
s = s[:start] + live_metrics + s[end:]

# Make management dialog use stabilized presentation too.
manage_start = s.find("function showManage(providerId) {")
manage_end = s.find("\nasync function loadCatalog()", manage_start)
if manage_start >= 0 and manage_end >= 0:
    block = s[manage_start:manage_end]
    block = block.replace(
        "  const telemetry = providerTelemetry(providerId) || {};\n  const runtimeState = lifecycle(provider);\n",
        "  const presentation = presentedRuntime(provider);\n  const telemetry = presentation.telemetry || {};\n  const runtimeState = presentation.state;\n",
        1,
    )
    s = s[:manage_start] + block + s[manage_end:]

js.write_text(s)

css_text = css.read_text()
marker = "/* SBP-041 — runtime status stabilization */"
if marker not in css_text:
    css_text += r'''

/* SBP-041 — runtime status stabilization */
.sync-progress-block {
  margin-top: 2px;
  padding: 12px 13px;
  border: 1px solid rgba(76,151,231,.20);
  border-radius: 12px;
  background: rgba(5,18,32,.55);
}

.sync-progress-block .progress-row {
  margin: 0;
}

.sync-progress-block .progress {
  height: 12px;
  margin-top: 7px;
  border: 1px solid rgba(77,156,255,.16);
  background: rgba(0,0,0,.42);
}

.sync-progress-block .progress i {
  min-width: 3px;
  box-shadow: 0 0 14px rgba(77,156,255,.25);
}

.sync-context {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-top: 9px;
  color: var(--muted);
  font-size: 12px;
}

.sync-context strong {
  color: var(--text);
  font-size: 12px;
}

.telemetry-grace-note {
  margin-top: 8px;
  padding: 8px 10px;
  border: 1px solid rgba(77,156,255,.22);
  border-radius: 9px;
  background: rgba(20,55,92,.38);
  color: #86c1ff;
  font-size: 11px;
}

.metric-good {
  color: #69e5b2;
  font-weight: 700;
}

.metric-bad {
  color: #ffb267;
  font-weight: 700;
}

.provider-card.syncing {
  border-color: rgba(77,156,255,.48);
  box-shadow:
    0 13px 30px rgba(0,0,0,.12),
    inset 0 0 0 1px rgba(77,156,255,.06);
}

.provider-card.syncing .status-pill::before {
  content: "";
  display: inline-block;
  width: 7px;
  height: 7px;
  margin-right: 7px;
  border-radius: 50%;
  background: #4d9cff;
  box-shadow: 0 0 9px rgba(77,156,255,.5);
}
'''
css.write_text(css_text)
