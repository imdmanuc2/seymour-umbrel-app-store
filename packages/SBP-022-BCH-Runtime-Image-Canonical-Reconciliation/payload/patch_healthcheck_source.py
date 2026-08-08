from pathlib import Path

root = Path("seymour-bch-node")
matches = []
for path in root.rglob("*"):
    if not path.is_file():
        continue
    try:
        text = path.read_text()
    except Exception:
        continue
    if "rpcwaittimeout=5 getblockchaininfo" in text:
        path.write_text(text.replace("rpcwaittimeout=5 getblockchaininfo", "rpcwaittimeout=5 uptime"))
        matches.append(str(path))

if not matches:
    print("No repository healthcheck source contained the legacy getblockchaininfo pattern.")
else:
    for item in matches:
        print(f"Patched healthcheck source: {item}")
