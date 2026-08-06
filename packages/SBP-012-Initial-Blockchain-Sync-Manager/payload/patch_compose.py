from pathlib import Path
path = Path("seymour-blockchain-manager/docker-compose.yml")
text = path.read_text()
anchor = "      INSTALL_OPERATION_DIRECTORY: /evidence/install-operations\n"
addition = anchor + "      SYNC_HISTORY_PATH: /evidence/sync-history.jsonl\n      SYNC_STALL_SECONDS: \"600\"\n      SYNC_LOW_PEERS: \"3\"\n"
if "SYNC_HISTORY_PATH" not in text:
    if anchor not in text:
        raise SystemExit("Expected installer environment anchor not found.")
    text = text.replace(anchor, addition, 1)
path.write_text(text)
print("Sync Manager environment added.")
