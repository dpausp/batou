# Stubs for cryptography.hazmat.primitives.serialization
# Minimal stubs for batou type checking

from typing import Any

class Encoding:
    PEM: Any

class PrivateFormat:
    OpenSSH: Any

class NoEncryption: ...

def load_ssh_private_key(data: bytes, password: bytes | None) -> Any: ...
