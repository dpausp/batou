import importlib
import sys

USE_LEGACY = None
_encrypt_module = None


def _pick_module():
    global _encrypt_module

    if _encrypt_module:
        return _encrypt_module

    module_hint = ".age_shellout" if USE_LEGACY else ".pyrage_encryption"

    try:
        _encrypt_module = importlib.import_module(module_hint, __name__)
    except ImportError:
        # Fall back to shellout if pyrage or its dependencies are missing
        _encrypt_module = importlib.import_module(".age_shellout", __name__)

    return _encrypt_module


def __getattr__(name):
    module = _pick_module()
    value = getattr(module, name)
    setattr(sys.modules[__name__], name, value)
    return value


def __dir__():
    return dir(_pick_module())
