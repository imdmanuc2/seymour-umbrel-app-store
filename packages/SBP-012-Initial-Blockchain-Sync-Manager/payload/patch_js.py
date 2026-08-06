from pathlib import Path
import re

path = Path("seymour-blockchain-manager/data/web/app.js")
text = path.read_text()

# Insert the Sync button directly before whichever button owns data-manage.
if 'data-sync="${provider.providerId}"' not in text:
    pattern = re.compile(
        r'(?P<indent>[ \t]*)<button\b'
        r'(?P<body>[\s\S]*?data-manage="\$\{provider\.providerId\}"[\s\S]*?</button>)'
    )

    match = pattern.search(text)

    if not match:
        raise SystemExit(
            "Could not locate the existing data-manage button."
        )

    indent = match.group("indent")
    manage_button = match.group(0)

    sync_button = (
        f'{indent}<button\n'
        f'{indent}  class="secondary"\n'
        f'{indent}  data-sync="${{provider.providerId}}"\n'
        f'{indent}>\n'
        f'{indent}  Sync\n'
        f'{indent}</button>\n'
    )

    text = (
        text[:match.start()]
        + sync_button
        + manage_button
        + text[match.end():]
    )

# Insert Sync event binding before the existing data-manage binding.
if 'querySelectorAll("[data-sync]")' not in text:
    marker = 'grid.querySelectorAll("[data-manage]")'
    position = text.find(marker)

    if position == -1:
        raise SystemExit(
            "Could not locate the existing data-manage event binding."
        )

    line_start = text.rfind("\n", 0, position) + 1
    indent = text[line_start:position]

    binding = (
        f'{indent}grid.querySelectorAll("[data-sync]").forEach((button) => {{\n'
        f'{indent}  button.addEventListener("click", () => {{\n'
        f'{indent}    showSyncManager(button.dataset.sync);\n'
        f'{indent}  }});\n'
        f'{indent}}});\n\n'
    )

    text = text[:line_start] + binding + text[line_start:]

path.write_text(text)

print("Sync Manager UI action added.")
