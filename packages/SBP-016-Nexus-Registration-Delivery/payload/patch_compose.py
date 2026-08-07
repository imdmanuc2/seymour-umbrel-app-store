from pathlib import Path

path = Path("seymour-blockchain-manager/docker-compose.yml")
text = path.read_text()

anchor = (
    "      NEXUS_REGISTRATION_EVIDENCE_PATH: "
    "/evidence/nexus-registration.jsonl\n"
)

addition = (
    anchor
    + "      NEXUS_REGISTRATION_URL: ${NEXUS_REGISTRATION_URL:-}\n"
    + "      NEXUS_REGISTRATION_TOKEN: ${NEXUS_REGISTRATION_TOKEN:-}\n"
    + "      NEXUS_REGISTRATION_TIMEOUT_SECONDS: \"15\"\n"
    + "      NEXUS_REGISTRATION_MAX_ATTEMPTS: \"4\"\n"
    + "      NEXUS_REGISTRATION_BACKOFF_SECONDS: \"2\"\n"
    + "      NEXUS_DELIVERY_EVIDENCE_PATH: /evidence/nexus-delivery.jsonl\n"
    + "      NEXUS_DELIVERY_STATUS_PATH: /evidence/nexus-delivery-status.json\n"
)

if "NEXUS_DELIVERY_EVIDENCE_PATH" not in text:
    if anchor not in text:
        raise SystemExit(
            "Expected Nexus registration environment anchor not found."
        )

    text = text.replace(
        anchor,
        addition,
        1,
    )

path.write_text(text)

print("Nexus registration delivery environment added.")
