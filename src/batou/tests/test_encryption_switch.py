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
    monkeypatch.setitem(sys.modules, "pyrage", None)

    sys.modules.pop("batou.secrets.encryption", None)
    from ..secrets.encryption import EncryptedFile

    assert EncryptedFile.__module__ == "batou.secrets.encryption.age_shellout"
