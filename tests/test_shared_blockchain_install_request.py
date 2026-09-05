from shared.blockchain_install.request import InstallRequest


def test_install_request_from_dict():
    request = InstallRequest.from_dict(
        {
            "providerId": "bitcoin-mainnet",
            "appId": "seymour-bitcoin-node",
            "nodeName": "Bitcoin Node",
            "rpcUser": "seymour_rpc",
            "rpcPassword": "x" * 32,
            "rpcPort": 8332,
            "p2pPort": 8333,
            "storageTargetId": "storage-1",
            "confirmation": (
                "INSTALL-seymour-bitcoin-node"
            ),
        }
    )

    assert request.provider_id == "bitcoin-mainnet"
    assert request.app_id == "seymour-bitcoin-node"
    assert request.storage_target_id == "storage-1"
    assert request.rpc_port == 8332
    assert request.p2p_port == 8333


def test_install_request_redacts_password():
    secret = "super-secret-value-that-must-not-leak"

    request = InstallRequest.from_dict(
        {
            "providerId": "bitcoin-mainnet",
            "appId": "seymour-bitcoin-node",
            "nodeName": "Bitcoin Node",
            "rpcUser": "seymour_rpc",
            "rpcPassword": secret,
            "rpcPort": 8332,
            "p2pPort": 8333,
            "storageTargetId": "storage-1",
            "confirmation": (
                "INSTALL-seymour-bitcoin-node"
            ),
        }
    )

    payload = request.redacted_dict()

    assert payload["rpcPassword"] == "[REDACTED]"
    assert secret not in str(payload)


def test_portable_manager_has_same_request_contract():
    canonical = open(
        "shared/blockchain_install/request.py"
    ).read()

    packaged = open(
        "seymour-blockchain-manager/"
        "data/shared/blockchain_install/request.py"
    ).read()

    assert packaged == canonical
