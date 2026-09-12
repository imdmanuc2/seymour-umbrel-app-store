from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]

WEB_ROOT = (
    ROOT
    / "seymour-blockchain-manager"
    / "data"
    / "web"
)


def load_nexus_control():
    root_text = str(ROOT)
    web_text = str(WEB_ROOT)

    if root_text not in sys.path:
        sys.path.insert(0, root_text)

    if web_text not in sys.path:
        sys.path.insert(0, web_text)

    path = WEB_ROOT / "nexus_control.py"

    spec = importlib.util.spec_from_file_location(
        "seymour_nexus_control_test",
        path,
    )

    if spec is None or spec.loader is None:
        raise RuntimeError(
            "Unable to load Nexus control adapter."
        )

    module = importlib.util.module_from_spec(
        spec
    )

    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    return module
