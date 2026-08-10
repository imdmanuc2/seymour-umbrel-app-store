from pathlib import Path
import sys

root = Path(sys.argv[1])
js = root / "seymour-blockchain-manager/data/web/app.js"

s = js.read_text()

# Add a tiny null-safe projection helper after top-level DOM bindings.
if "function setText(id, value)" not in s:
    anchor = 'const dialogContent = document.getElementById("dialogContent");\n'
    if anchor not in s:
        raise SystemExit("SBP-042.1 patch: dialogContent anchor missing")
    helper = '''const dialogContent = document.getElementById("dialogContent");

function setText(id, value) {
  const node = document.getElementById(id);
  if (node) node.textContent = value;
}
'''
    s = s.replace(anchor, helper, 1)

# Make renderHost resilient to future layout changes.
replacements = {
'''  document.getElementById("hostCpu").textContent =
    `${Number(host.cpuPercent || 0).toFixed(1)}%`;
''':
'''  setText(
    "hostCpu",
    `${Number(host.cpuPercent || 0).toFixed(1)}%`
  );
''',
'''  document.getElementById("hostMemory").textContent =
    `${Number(host.memory?.usedPercent || 0).toFixed(1)}%`;
''':
'''  setText(
    "hostMemory",
    `${Number(host.memory?.usedPercent || 0).toFixed(1)}%`
  );
''',
'''  document.getElementById("hostStorage").textContent =
    formatBytes(host.storage?.freeBytes);
''':
'''  setText(
    "hostStorage",
    formatBytes(host.storage?.freeBytes)
  );
''',
'''  document.getElementById("hostDocker").textContent =
    host.docker?.available ? "Online" : "Unavailable";
''':
'''  setText(
    "hostDocker",
    host.docker?.available ? "Online" : "Unavailable"
  );
''',
'''  document.getElementById("hostArchitecture").textContent =
    host.architecture || "—";
''':
'''  setText(
    "hostArchitecture",
    host.architecture || "—"
  );
''',
}
for old, new in replacements.items():
    if old in s:
        s = s.replace(old, new, 1)

# hostPanel itself is optional presentation chrome, so guard it.
old_host_panel = '''  document.getElementById("hostPanel").classList.toggle(
    "warning",
    !host.healthy
  );
'''
new_host_panel = '''  document.getElementById("hostPanel")?.classList.toggle(
    "warning",
    !host.healthy
  );
'''
if old_host_panel in s:
    s = s.replace(old_host_panel, new_host_panel, 1)

# Replace loadCatalog's legacy summary writes.
start = s.find("async function loadCatalog() {")
end = s.find("\nasync function refreshTelemetry()", start)
if start < 0 or end < 0:
    raise SystemExit("SBP-042.1 patch: loadCatalog anchors missing")

block = s[start:end]

# Delete all writes to removed SBP-000-era catalog summary IDs.
import re
block = re.sub(
    r'\n\s*const live = state\.providers\.filter\([\s\S]*?\)\.length;\n'
    r'\s*document\.getElementById\("providerCount"\)\.textContent =\n'
    r'\s*payload\.providerCount;\n'
    r'\s*document\.getElementById\("liveCount"\)\.textContent = live;\n'
    r'\s*document\.getElementById\("plannedCount"\)\.textContent =\n'
    r'\s*payload\.providerCount - live;\n',
    "\n",
    block,
    count=1,
)

block = block.replace(
'''  document.getElementById("catalogStatus").textContent =
    `Catalog ${payload.catalogVersion} · Live telemetry`;
''',
'''  setText(
    "catalogStatus",
    `Catalog ${payload.catalogVersion} · Live telemetry`
  );
''',
1,
)

s = s[:start] + block + s[end:]

# Error banner must not crash either.
old_error = '''    document.getElementById("catalogStatus").textContent =
      `Telemetry error: ${error.message}`;
'''
new_error = '''    setText(
      "catalogStatus",
      `Telemetry error: ${error.message}`
    );
'''
if old_error in s:
    s = s.replace(old_error, new_error, 1)

js.write_text(s)
