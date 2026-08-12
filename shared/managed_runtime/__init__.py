from .adapter import ManagedRuntimeAdapter
from .models import ManagedRuntimeCapabilities, ManagedRuntimeIdentity, ManagedRuntimeObservation
from .registry import ManagedRuntimeAdapterRegistry
from .umbrel import UmbrelManagedRuntimeAdapter

__all__ = [
    "ManagedRuntimeAdapter",
    "ManagedRuntimeCapabilities",
    "ManagedRuntimeIdentity",
    "ManagedRuntimeObservation",
    "ManagedRuntimeAdapterRegistry",
    "UmbrelManagedRuntimeAdapter",
]

from .registration import (
    REGISTRATION_CONTRACT,
    REGISTRATION_VERSION,
    attach_managed_runtime_projection,
    project_asset,
    project_registration_payload,
)

__all__ += [
    "REGISTRATION_CONTRACT",
    "REGISTRATION_VERSION",
    "attach_managed_runtime_projection",
    "project_asset",
    "project_registration_payload",
]
