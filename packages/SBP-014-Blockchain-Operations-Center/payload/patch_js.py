from pathlib import Path

path = Path("seymour-blockchain-manager/data/web/app.js")
text = path.read_text()

# Add Operations button before the existing Adopt button.
if 'data-operations="${provider.providerId}"' not in text:
    marker = 'data-adopt="${provider.providerId}"'
    marker_position = text.find(marker)

    if marker_position == -1:
        raise SystemExit(
            "Could not locate the existing data-adopt button."
        )

    button_start = text.rfind("<button", 0, marker_position)

    if button_start == -1:
        raise SystemExit(
            "Could not locate the start of the Adopt button."
        )

    line_start = text.rfind("\n", 0, button_start) + 1
    indent = text[line_start:button_start]

    operations_button = (
        f'{indent}<button\n'
        f'{indent}  class="secondary"\n'
        f'{indent}  data-operations="${{provider.providerId}}"\n'
        f'{indent}>\n'
        f'{indent}  Operations\n'
        f'{indent}</button>\n'
    )

    text = (
        text[:button_start]
        + operations_button
        + text[button_start:]
    )

# Add Operations event binding before the existing Adopt binding.
if 'querySelectorAll("[data-operations]")' not in text:
    marker = 'grid.querySelectorAll("[data-adopt]")'
    marker_position = text.find(marker)

    if marker_position == -1:
        raise SystemExit(
            "Could not locate the existing data-adopt event binding."
        )

    line_start = text.rfind("\n", 0, marker_position) + 1
    indent = text[line_start:marker_position]

    operations_binding = (
        f'{indent}grid.querySelectorAll("[data-operations]").forEach((button) => {{\n'
        f'{indent}  button.addEventListener("click", () => {{\n'
        f'{indent}    showOperationsCenter(button.dataset.operations);\n'
        f'{indent}  }});\n'
        f'{indent}}});\n\n'
    )

    text = (
        text[:line_start]
        + operations_binding
        + text[line_start:]
    )

path.write_text(text)

print("Blockchain Operations Center UI action added.")
