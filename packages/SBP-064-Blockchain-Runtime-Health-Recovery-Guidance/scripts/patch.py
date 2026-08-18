#!/usr/bin/env python3
from pathlib import Path
import sys
repo = Path(sys.argv[1])
telemetry = repo / "seymour-blockchain-manager/data/web/telemetry.py"
app = repo / "seymour-blockchain-manager/data/web/app.js"

text = telemetry.read_text()
if "from runtime_health import runtime_health" not in text:
    anchor = "from runtime_registry import dashboard_runtimes\n"
    if anchor not in text:
        raise SystemExit("telemetry import anchor not found")
    text = text.replace(anchor, anchor + "from runtime_health import runtime_health\n", 1)

if '"health": health' not in text:
    marker = '    return {\n        "providerId": "bitcoin-cash-mainnet",\n'
    if marker not in text:
        raise SystemExit("BCH telemetry return anchor not found")
    insert = '''    health = runtime_health(\n        runtime_state=runtime_state,\n        rpc_reachable=rpc_reachable,\n        rpc_healthy=rpc_healthy,\n        sync=sync,\n        sync_analysis={},\n        storage=storage,\n        telemetry_stale=bool(runtime.get("telemetryStale")),\n        runtime_reason=operational_state.get("reason"),\n    )\n\n'''
    text = text.replace(marker, insert + marker, 1)
    target = '        "runtimeStateReason": operational_state.get("reason"),\n'
    if target not in text:
        raise SystemExit("runtimeStateReason anchor not found")
    text = text.replace(target, target + '        "health": health,\n', 1)
telemetry.write_text(text)

js = app.read_text()
if "function runtimeHealthGuidance(" not in js:
    anchor = "function lifecycleLabel(value) {\n"
    if anchor not in js:
        raise SystemExit("lifecycleLabel anchor not found")
    helper = '''function runtimeHealthGuidance(telemetry = {}) {\n  const health = telemetry?.health || {};\n  return {\n    state: health.state || "unknown",\n    reasonCode: health.reasonCode || "runtime-unknown",\n    summary: health.summary || "Runtime health is unknown.",\n    detail: health.detail || "Run diagnostics for more information.",\n    recommendedAction: health.recommendedAction || "diagnostics",\n    destructive: health.destructive === true,\n  };\n}\n\nfunction healthStateLabel(value) {\n  return {healthy: "Healthy", warning: "Attention", critical: "Critical", unknown: "Unknown"}[value] || value;\n}\n\n'''
    js = js.replace(anchor, helper + anchor, 1)

# Manage dialog: add health variable after progress block.
manage_sig = "function showManage(providerId) {"
pos = js.find(manage_sig)
if pos < 0:
    raise SystemExit("showManage not found")
segment = js[pos:]
if "const health = runtimeHealthGuidance(telemetry);" not in segment.split("function ", 1)[0]:
    anchor = '      : "—";\n\n  dialogContent.innerHTML = `\n'
    idx = segment.find(anchor)
    if idx < 0:
        raise SystemExit("Manage health insertion anchor not found")
    segment = segment[:idx] + '      : "—";\n  const health = runtimeHealthGuidance(telemetry);\n\n  dialogContent.innerHTML = `\n' + segment[idx+len(anchor):]
    js = js[:pos] + segment

if "runtime-guidance-card" not in js[js.find(manage_sig):js.find("function ", js.find(manage_sig)+1) if js.find("function ", js.find(manage_sig)+1)>0 else len(js)]:
    pos = js.find(manage_sig)
    segment = js[pos:]
    anchor = '    <div class="manage-grid">\n'
    card = '''    <section class="runtime-guidance-card ${health.state}">\n      <div class="runtime-guidance-heading">\n        <strong>${health.summary}</strong>\n        <span class="status-pill">${healthStateLabel(health.state)}</span>\n      </div>\n      <p>${health.detail}</p>\n      <small>Reason: ${health.reasonCode} · Recommended action: ${health.recommendedAction}</small>\n    </section>\n\n'''
    if anchor not in segment:
        raise SystemExit("manage-grid anchor not found")
    segment = segment.replace(anchor, card + anchor, 1)
    js = js[:pos] + segment

ops_sig = "async function showOperationsCenter(providerId) {"
pos = js.find(ops_sig)
if pos < 0:
    raise SystemExit("Operations Center not found")
segment = js[pos:]
if "const health = runtimeHealthGuidance(telemetry);" not in segment[:segment.find("dialogContent.innerHTML")]:
    anchor = '      : "—";\n\n  dialogContent.innerHTML = `\n'
    idx = segment.find(anchor)
    if idx < 0:
        raise SystemExit("Operations health insertion anchor not found")
    segment = segment[:idx] + '      : "—";\n  const health = runtimeHealthGuidance(telemetry);\n\n  dialogContent.innerHTML = `\n' + segment[idx+len(anchor):]
    js = js[:pos] + segment

if "ops-health-guidance" not in js:
    pos = js.find(ops_sig)
    segment = js[pos:]
    anchor = '      <section class="ops-section">\n        <div class="ops-section-heading">\n          <div>\n            <p class="eyebrow">Diagnostics</p>\n'
    card = '''      <section class="ops-section ops-health-guidance">\n        <div class="runtime-guidance-card ${health.state}">\n          <div class="runtime-guidance-heading">\n            <strong>${health.summary}</strong>\n            <span class="status-pill">${healthStateLabel(health.state)}</span>\n          </div>\n          <p>${health.detail}</p>\n          <small>Reason: ${health.reasonCode} · Recommended action: ${health.recommendedAction}</small>\n        </div>\n      </section>\n\n'''
    if anchor not in segment:
        raise SystemExit("Operations diagnostics anchor not found")
    segment = segment.replace(anchor, card + anchor, 1)
    js = js[:pos] + segment

app.write_text(js)
print("SBP-064 source patch: PASS")
