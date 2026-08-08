from pathlib import Path

path = Path("seymour-bch-node/docker-compose.yml")
text = path.read_text()

if "/usr/local/bin/seymour-entrypoint" not in text:
    raise SystemExit("Expected canonical entrypoint bind mount is missing from BCH compose.")

if 'entrypoint: ["/usr/local/bin/seymour-entrypoint"]' not in text:
    marker = "  node:\n"
    if marker not in text:
        raise SystemExit("Could not locate BCH node service.")
    text = text.replace(marker, marker + '    entrypoint: ["/usr/local/bin/seymour-entrypoint"]\n', 1)

path.write_text(text)
print("BCH compose canonical entrypoint override added.")
