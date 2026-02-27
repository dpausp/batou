# Stubs for pyrage library
# https://pypi.org/project/pyrage/

class RecipientError(Exception): ...

class Identity:
    @classmethod
    def from_buffer(cls, data: bytes) -> Identity: ...

class Recipient:
    @classmethod
    def from_str(cls, s: str) -> Recipient: ...

class ssh:  # noqa: N801
    Identity = Identity
    Recipient = Recipient

def encrypt(plaintext: bytes, recipients: list[Recipient]) -> bytes: ...
def decrypt(ciphertext: bytes, identities: list[Identity]) -> bytes: ...
