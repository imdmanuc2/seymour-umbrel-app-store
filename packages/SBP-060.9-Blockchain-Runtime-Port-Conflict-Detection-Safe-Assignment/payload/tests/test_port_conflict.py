from blockchain_recovery.port_guard import first_free_port

def test_empty_candidates():
    assert first_free_port([]) is None
