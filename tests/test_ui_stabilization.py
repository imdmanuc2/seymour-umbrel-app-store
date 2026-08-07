from pathlib import Path
import re

repo = Path(__file__).resolve().parents[1]
path = repo / "seymour-blockchain-manager/data/web/app.js"
text = path.read_text()

filters = re.search(
    r"function renderFilters\(\).*?\n\}",
    text,
    re.DOTALL,
)
providers = re.search(
    r"function renderProviders\(\).*?\n\}",
    text,
    re.DOTALL,
)

assert filters is not None
assert providers is not None

filters_text = filters.group(0)
providers_text = providers.group(0)

assert "provider.providerId" not in filters_text
assert 'data-family="${family}"' in filters_text
assert 'querySelectorAll("[data-family]")' in filters_text

buttons = (
    'data-details="${provider.providerId}"',
    'data-sync="${provider.providerId}"',
    'data-adopt="${provider.providerId}"',
    'data-operations="${provider.providerId}"',
    'data-manage="${provider.providerId}"',
)

bindings = (
    'querySelectorAll("[data-details]")',
    'querySelectorAll("[data-sync]")',
    'querySelectorAll("[data-adopt]")',
    'querySelectorAll("[data-operations]")',
    'querySelectorAll("[data-manage]")',
)

for marker in buttons + bindings:
    assert marker in providers_text
    assert text.count(marker) == 1

for function in (
    "showDetails",
    "showManage",
    "showSyncManager",
    "showAdoptionWizard",
    "showOperationsCenter",
):
    assert (
        f"function {function}" in text
        or f"async function {function}" in text
    )

print("SBP-014A UI stabilization verification: PASS")
