from pathlib import Path
path = Path("seymour-blockchain-manager/docker-compose.yml")
text = path.read_text()
anchor = "      LIFECYCLE_EVIDENCE_PATH: /evidence/lifecycle.jsonl\n"
addition = anchor + "      SEYMOUR_BCH_INSTALL_SCRIPT: /control/seymour-install-bch\n      INSTALL_EVIDENCE_PATH: /evidence/installations.jsonl\n      INSTALL_OPERATION_DIRECTORY: /evidence/install-operations\n"
if "SEYMOUR_BCH_INSTALL_SCRIPT" not in text:
    if anchor not in text:
        raise SystemExit("Expected lifecycle environment anchor not found.")
    text = text.replace(anchor, addition, 1)
path.write_text(text)
print("Blockchain Manager installation environment added.")
