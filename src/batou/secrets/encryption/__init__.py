import importlib
import sys

from batou import output

USE_LEGACY = None
_encrypt_module = None
_backend_name = None


def get_backend_name():
    """Return the name of the encryption backend in use."""
    _pick_module()  # Ensure module is loaded
    return _backend_name


def _pick_module():
    global _encrypt_module, _backend_name

    if _encrypt_module:
        return _encrypt_module

    module_hint = ".age_shellout" if USE_LEGACY else ".pyrage_encryption"

    try:
        _encrypt_module = importlib.import_module(module_hint, __name__)
        _backend_name = (
            "pyrage" if module_hint == ".pyrage_encryption" else "age (shellout)"
        )
    except ImportError:
        # Fall back to shellout if pyrage or its dependencies are missing
        _encrypt_module = importlib.import_module(".age_shellout", __name__)
        _backend_name = "age (shellout)"

    output.step("secrets", f"Using {_backend_name} backend", icon="🔐")

    return _encrypt_module


def __getattr__(name):
    module = _pick_module()
    value = getattr(module, name)
    setattr(sys.modules[__name__], name, value)
    return value


def __dir__():
    return dir(_pick_module())
