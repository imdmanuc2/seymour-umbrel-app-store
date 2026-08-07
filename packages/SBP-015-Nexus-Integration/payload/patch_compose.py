from pathlib import Path

path = Path("seymour-blockchain-manager/docker-compose.yml")
text = path.read_text()

anchor = "      BCH_NODE_CONTAINER: seymour-bch-node_node_1\n"
addition = (
    anchor
    + "      NEXUS_REGISTRATION_EVIDENCE_PATH: /evidence/nexus-registration.jsonl\n"
)

if "NEXUS_REGISTRATION_EVIDENCE_PATH" not in text:
    if anchor not in text:
        raise SystemExit("Expected Operations Center environment anchor not found.")
    text = text.replace(anchor, addition, 1)

path.write_text(text)
print("Nexus integration environment added.")
