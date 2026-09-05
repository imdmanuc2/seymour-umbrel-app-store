from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class InstallRequest:
    """
    Provider-neutral Seymour blockchain runtime installation request.

    This contract belongs to the shared blockchain-install layer rather
    than any particular management UI. Blockchain Manager and Nexus may
    both construct this request while the target runtime installation
    service remains the execution owner.
    """

    provider_id: str
    app_id: str
    node_name: str
    rpc_user: str
    rpc_password: str
    rpc_port: int
    p2p_port: int
    storage_target_id: str
    confirmation: str

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "InstallRequest":
        return cls(
            provider_id=str(
                data.get("providerId", "")
            ).strip(),
            app_id=str(
                data.get("appId", "")
            ).strip(),
            node_name=str(
                data.get("nodeName", "")
            ).strip(),
            rpc_user=str(
                data.get("rpcUser", "")
            ).strip(),
            rpc_password=str(
                data.get("rpcPassword", "")
            ),
            rpc_port=int(
                data.get("rpcPort", 8332)
            ),
            p2p_port=int(
                data.get("p2pPort", 8333)
            ),
            storage_target_id=str(
                data.get("storageTargetId", "")
            ).strip(),
            confirmation=str(
                data.get("confirmation", "")
            ),
        )

    def redacted_dict(self) -> dict[str, Any]:
        return {
            "providerId": self.provider_id,
            "appId": self.app_id,
            "nodeName": self.node_name,
            "rpcUser": self.rpc_user,
            "rpcPassword": "[REDACTED]",
            "rpcPort": self.rpc_port,
            "p2pPort": self.p2p_port,
            "storageTargetId": self.storage_target_id,
            "confirmation": self.confirmation,
        }
