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

anchor = """  web:
    image: python:3.12-alpine
"""
replacement = """  web:
    image: python:3.12-alpine
    networks:
      default:
        aliases:
          - seymour-blockchain-manager-web
"""
if "          - seymour-blockchain-manager-web\\n" not in text:
    if anchor not in text:
        raise SystemExit("SBP-060.2 web alias anchor not found")
    text = text.replace(anchor, replacement, 1)

path.write_text(text)
print("SBP-060.2 unique proxy DNS target: PASS")
