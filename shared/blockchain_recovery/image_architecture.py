from __future__ import annotations

from typing import Any

from runtime_architecture import architecture_report


def image_architecture_finding_payload(image: str) -> dict[str, Any]:
    report = architecture_report(image).to_dict()
    return {
        "conflict": not bool(report.get("compatible")),
        **report,
    }
