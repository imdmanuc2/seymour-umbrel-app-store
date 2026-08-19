#!/usr/bin/env python3
from pathlib import Path
import sys

path = Path(sys.argv[1])
lines = path.read_text().splitlines()

out = []
i = 0
removed = False

while i < len(lines):
    line = lines[i]

    if (
        i + 1 < len(lines)
        and line.strip() == "runtime-images/monero/staged/monerod \\"
        and lines[i + 1].strip() == "--version"
    ):
        indent = line[: len(line) - len(line.lstrip())]
        out.extend([
            indent + "# Do not execute the staged binary here.",
            indent + "# The GitHub runner is amd64; arm64 execution is",
            indent + "# verified later after QEMU/Buildx setup.",
        ])
        i += 2
        removed = True
        continue

    out.append(line)
    i += 1

if not removed and not any(
    "Do not execute the staged binary here." in line for line in lines
):
    raise SystemExit("ERROR: staged monerod execution anchor not found")

path.write_text("\n".join(out) + "\n")
print("SBP-071.1 Monero prestage architecture repair: PASS")
