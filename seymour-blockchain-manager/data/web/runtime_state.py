from __future__ import annotations

import os
import sys
from pathlib import Path

platform_root = Path(os.environ.get("SEYMOUR_PLATFORM_ROOT", "/seymour-platform"))
root_text = str(platform_root)
if root_text not in sys.path:
    sys.path.insert(0, root_text)

from shared.runtime_state import (
    CANONICAL_RUNTIME_STATES,
    RuntimeStateService,
    normalize_runtime_state,
)

VALID_RUNTIME_STATES = set(CANONICAL_RUNTIME_STATES)

__all__ = [
    "CANONICAL_RUNTIME_STATES",
    "VALID_RUNTIME_STATES",
    "RuntimeStateService",
    "normalize_runtime_state",
]
