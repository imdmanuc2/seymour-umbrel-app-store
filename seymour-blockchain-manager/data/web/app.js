const state = {
  providers: [],
  family: "all",
  query: "",
};

const grid = document.getElementById("providerGrid");
const filters = document.getElementById("filters");
const search = document.getElementById("search");
const dialog = document.getElementById("providerDialog");
const dialogContent = document.getElementById("dialogContent");

function formatBytes(value) {
  const units = ["B", "KB", "MB", "GB", "TB"];
  let size = Number(value);
  let index = 0;

  while (size >= 1000 && index < units.length - 1) {
    size /= 1000;
    index += 1;
  }

  return `${size.toFixed(index > 2 ? 1 : 0)} ${units[index]}`;
}

function statusLabel(provider) {
  if (provider.availability === "live") {
    return "Available";
  }
  if (provider.availability === "disabled") {
    return "Unavailable";
  }
  return "Coming soon";
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
    ]
      .join(" ")
      .toLowerCase();

    const queryMatch = haystack.includes(
      state.query.toLowerCase()
    );

    return familyMatch && queryMatch;
  });
}

function renderFilters() {
  const families = [
    "all",
    ...new Set(
      state.providers.map((provider) => provider.family)
    ),
  ];

  filters.innerHTML = families
    .map(
      (family) => `
        <button
          class="${family === state.family ? "active" : ""}"
          data-family="${family}"
        >
          ${family === "all" ? "All" : family}
        </button>
      `
    )
    .join("");

  filters.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      state.family = button.dataset.family;
      renderFilters();
      renderProviders();
    });
  });
}

function renderProviders() {
  const providers = filteredProviders();

  if (!providers.length) {
    grid.innerHTML = `
      <p class="empty">
        No providers match the current filters.
      </p>
    `;
    return;
  }

  grid.innerHTML = providers
    .map(
      (provider) => `
        <article class="provider-card ${provider.availability}">
          <div class="card-top">
            <div class="coin-badge">${provider.ticker}</div>
            <span class="status-pill">${statusLabel(provider)}</span>
          </div>

          <div>
            <p class="provider-family">${provider.family}</p>
            <h2>${provider.displayName}</h2>
            <p class="implementation">
              ${provider.implementation} ${provider.nodeVersion}
            </p>
          </div>

          <dl class="metadata">
            <div>
              <dt>Mining</dt>
              <dd>${provider.miningAlgorithm}</dd>
            </div>
            <div>
              <dt>Disk estimate</dt>
              <dd>${formatBytes(provider.estimatedDiskBytes)}</dd>
            </div>
            <div>
              <dt>Architecture</dt>
              <dd>${provider.supportedArchitectures.join(" · ")}</dd>
            </div>
          </dl>

          <div class="card-actions">
            <button
              class="secondary"
              data-details="${provider.providerId}"
            >
              View details
            </button>

            ${
              provider.selectable
                ? `
                  <button
                    class="primary"
                    data-install="${provider.providerId}"
                  >
                    ${provider.installAction?.label || "Install"}
                  </button>
                `
                : `
                  <button class="disabled" disabled>
                    Coming soon
                  </button>
                `
            }
          </div>
        </article>
      `
    )
    .join("");

  grid.querySelectorAll("[data-details]").forEach((button) => {
    button.addEventListener("click", () => {
      showDetails(button.dataset.details);
    });
  });

  grid.querySelectorAll("[data-install]").forEach((button) => {
    button.addEventListener("click", () => {
      const provider = state.providers.find(
        (item) => item.providerId === button.dataset.install
      );

      showInstallAction(provider);
    });
  });
}

function showDetails(providerId) {
  const provider = state.providers.find(
    (item) => item.providerId === providerId
  );

  const ports = Object.entries(provider.defaultPorts)
    .map(([name, port]) => `<li><strong>${name}</strong>: ${port}</li>`)
    .join("");

  dialogContent.innerHTML = `
    <p class="provider-family">${provider.family}</p>
    <h2>${provider.displayName} <span>${provider.ticker}</span></h2>
    <p>${provider.implementation} ${provider.nodeVersion}</p>

    <dl class="dialog-metadata">
      <div><dt>Status</dt><dd>${statusLabel(provider)}</dd></div>
      <div><dt>Network</dt><dd>${provider.network}</dd></div>
      <div><dt>Mining algorithm</dt><dd>${provider.miningAlgorithm}</dd></div>
      <div><dt>Estimated disk</dt><dd>${formatBytes(provider.estimatedDiskBytes)}</dd></div>
      <div><dt>Architectures</dt><dd>${provider.supportedArchitectures.join(", ")}</dd></div>
    </dl>

    <h3>Default ports</h3>
    <ul>${ports}</ul>

    ${
      provider.selectable
        ? `<p class="available-note">This provider is ready for installation.</p>`
        : `<p class="planned-note">This provider is in the Version 1.0 catalog, but its production image and install workflow are not ready yet.</p>`
    }
  `;

  dialog.showModal();
}

function showInstallAction(provider) {
  dialogContent.innerHTML = `
    <p class="provider-family">installation</p>
    <h2>${provider.displayName}</h2>
    <p>
      The catalog has validated this provider as installable.
    </p>
    <div class="install-contract">
      <code>App ID: ${provider.installAction.appId}</code>
      <code>Image: ${provider.productionImage}</code>
    </div>
    <p>
      The next package will connect this action to the guarded BCH
      installation workflow.
    </p>
  `;

  dialog.showModal();
}

async function loadProviders() {
  const response = await fetch("/api/providers");

  if (!response.ok) {
    throw new Error(`Catalog request failed: ${response.status}`);
  }

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
    `Catalog ${payload.catalogVersion} · Frozen`;

  renderFilters();
  renderProviders();
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
  if (event.target === dialog) {
    dialog.close();
  }
});

loadProviders().catch((error) => {
  grid.innerHTML = `
    <p class="error">
      Unable to load provider catalog: ${error.message}
    </p>
  `;
});
