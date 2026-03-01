import sys

import pytest


def _pyrage_available():
    """Check if pyrage and its dependencies are actually importable."""
    try:
        import pyrage  # noqa: F401

        # Also check cryptography which pyrage_encryption needs
        from cryptography.hazmat.primitives import serialization  # noqa: F401
    except ImportError:
        return False
    return True


_pyrage_is_available = _pyrage_available()


@pytest.mark.skipif(not _pyrage_is_available, reason="requires pyrage")
def test_import_pyrage_encryption():
    from ..secrets.encryption import EncryptedFile

    assert EncryptedFile.__module__ == "batou.secrets.encryption.pyrage_encryption"


@pytest.mark.skipif(not _pyrage_is_available, reason="requires pyrage")
def test_import_legacy_encryption(monkeypatch):
    import batou.secrets.encryption as enc_mod

    # Reset cached module state
    enc_mod._encrypt_module = None
    enc_mod._backend_name = None

    # Remove all encryption modules from cache to force re-import
    for key in list(sys.modules.keys()):
        if key.startswith("batou.secrets.encryption"):
            sys.modules.pop(key, None)

    # Simulate pyrage being unavailable
    monkeypatch.setitem(sys.modules, "pyrage", None)

    from ..secrets.encryption import EncryptedFile

    assert EncryptedFile.__module__ == "batou.secrets.encryption.age_shellout"
