from pathlib import Path
import sys

repo = Path(sys.argv[1])
path = repo / "seymour-bch-node/data/status/Dockerfile"
text = path.read_text()

if "COPY provisioning.py" not in text:
    text = text.replace(
        "COPY app.py /app/app.py\n",
        "COPY app.py /app/app.py\nCOPY provisioning.py /app/provisioning.py\n",
    )

if "COPY templates" not in text:
    text += "\nCOPY templates /app/templates\n"

path.write_text(text)
