from bitcoin_managed_runtime.architecture import normalize_architecture

def test_architecture_normalization():
    assert normalize_architecture("x86_64") == "amd64"
    assert normalize_architecture("amd64") == "amd64"
    assert normalize_architecture("aarch64") == "arm64"
    assert normalize_architecture("arm64") == "arm64"
