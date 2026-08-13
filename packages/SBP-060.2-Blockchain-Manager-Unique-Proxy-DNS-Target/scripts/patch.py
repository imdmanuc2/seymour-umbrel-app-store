#!/usr/bin/env python3
from pathlib import Path
import sys

repo = Path(sys.argv[1]).resolve()
path = repo / "seymour-blockchain-manager/docker-compose.yml"
text = path.read_text()

old = "      APP_HOST: web\n"
new = "      APP_HOST: seymour-blockchain-manager_web_1\n"

if old in text:
    text = text.replace(old, new, 1)
elif new not in text:
    raise SystemExit("SBP-060.2 APP_HOST anchor not found")

path.write_text(text)
print("SBP-060.2 unique proxy DNS target: PASS")
