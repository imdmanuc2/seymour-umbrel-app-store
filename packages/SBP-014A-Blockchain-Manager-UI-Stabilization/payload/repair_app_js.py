from pathlib import Path
import re

path = Path("seymour-blockchain-manager/data/web/app.js")
text = path.read_text()

backup = path.with_suffix(".js.before-sbp-014a")
backup.write_text(text)

def replace_function(source, name, replacement):
    pattern = re.compile(
        rf"function {re.escape(name)}\([^)]*\) \{{.*?\n\}}",
        re.DOTALL,
    )
    match = pattern.search(source)
    if not match:
        raise SystemExit(f"Could not locate function: {name}")
    return source[:match.start()] + replacement.rstrip() + source[match.end():]

render_filters = r'''
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
'''

render_providers = r'''
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
          <button class="secondary" data-details="${provider.providerId}">
            View details
          </button>

          ${
            provider.selectable
              ? `
                <button class="secondary" data-sync="${provider.providerId}">
                  Sync
                </button>
                <button class="secondary" data-adopt="${provider.providerId}">
                  Adopt
                </button>
                <button class="secondary" data-operations="${provider.providerId}">
                  Operations
                </button>
                <button class="primary" data-manage="${provider.providerId}">
                  Manage
                </button>
              `
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
'''

text = replace_function(text, "renderFilters", render_filters)
text = replace_function(text, "renderProviders", render_providers)

required_functions = (
    "showDetails",
    "showManage",
    "showSyncManager",
    "showAdoptionWizard",
    "showOperationsCenter",
)

missing = [
    name
    for name in required_functions
    if f"function {name}" not in text
    and f"async function {name}" not in text
]

if missing:
    raise SystemExit(
        "Required UI functions are missing: " + ", ".join(missing)
    )

for marker in (
    'data-sync="${provider.providerId}"',
    'data-adopt="${provider.providerId}"',
    'data-operations="${provider.providerId}"',
    'data-manage="${provider.providerId}"',
    'querySelectorAll("[data-sync]")',
    'querySelectorAll("[data-adopt]")',
    'querySelectorAll("[data-operations]")',
    'querySelectorAll("[data-manage]")',
):
    count = text.count(marker)
    if count != 1:
        raise SystemExit(
            f"Expected one occurrence of {marker!r}; found {count}"
        )

filters_match = re.search(
    r"function renderFilters\(\).*?\n\}",
    text,
    re.DOTALL,
)
if not filters_match:
    raise SystemExit("Repaired renderFilters is missing.")
if "provider.providerId" in filters_match.group(0):
    raise SystemExit("renderFilters still contains provider action markup.")

path.write_text(text)

print(f"Backup: {backup}")
print("Blockchain Manager app.js stabilized.")
