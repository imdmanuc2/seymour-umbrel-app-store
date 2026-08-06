from pathlib import Path
path = Path("seymour-blockchain-manager/docker-compose.yml")
text = path.read_text()
anchor = '      SYNC_LOW_PEERS: "3"\n'
addition = anchor + '      BCH_MANAGED_DATA_PATH: /adopted-bch-data\n      ADOPTION_EVIDENCE_PATH: /evidence/adoptions.jsonl\n      ADOPTION_PLAN_DIRECTORY: /evidence/adoption-plans\n'
if "ADOPTION_EVIDENCE_PATH" not in text:
    if anchor not in text:
        raise SystemExit("Expected sync environment anchor not found.")
    text = text.replace(anchor, addition, 1)
volume_anchor = '      - /home/umbrel/umbrel/app-data/seymour-bch-node/data/node:/bch-data:ro\n'
if "/adopted-bch-data" not in text:
    if volume_anchor not in text:
        raise SystemExit("Expected BCH volume anchor not found.")
    text = text.replace(volume_anchor, volume_anchor + '      - ${APP_DATA_DIR}/data/adopted-bch:/adopted-bch-data\n', 1)
path.write_text(text)
print("Existing-node adoption environment added.")
