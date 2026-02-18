import pathlib
import types

debug: bool

def expect(fd: int, expected: bytes) -> tuple[bool, bytes]: ...
def get_identities() -> list[str]: ...
def get_encrypted_file(path: pathlib.Path, writeable: bool = ...) -> EncryptedFile: ...

class EncryptedFile:
    path: pathlib.Path
    writeable: bool
    fd: int | None
    is_new: bool | None
    file_ending: str | None

    def __enter__(
        self,
    ) -> "AGEEncryptedFile | DiffableAGEEncryptedFile | GPGEncryptedFile": ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: types.TracebackType | None,
    ) -> bool | None: ...
    def __init__(self, path: pathlib.Path, writeable: bool = ...) -> None: ...
    def _lock(self) -> None: ...
    def _unlock(self) -> None: ...
    @property
    def cleartext(self) -> str: ...
    @property
    def decrypted(self) -> bytes: ...
    @property
    def locked(self) -> bool: ...
    def write(
        self,
        content: bytes,
        recipients: list[str],
        reencrypt: bool = ...,
    ) -> None: ...
    def decrypt(self) -> bytes: ...

class AGEEncryptedFile(EncryptedFile):
    file_ending: str

    def _write(
        self,
        content: bytes,
        recipients: list[str],
        reencrypt: bool = ...,
    ) -> None: ...
    @classmethod
    def age(cls) -> str: ...

class DiffableAGEEncryptedFile(EncryptedFile):
    def _write(
        self,
        content: bytes,
        recipients: list[str],
        reencrypt: bool = ...,
    ) -> None: ...
    def decrypt_age_string(self, content: str) -> str: ...
    def encrypt_age_string(self, content: str, recipients: list[str]) -> str: ...

class GPGEncryptedFile(EncryptedFile):
    file_ending: str

    def _write(
        self,
        content: bytes,
        recipients: list[str],
        reencrypt: bool = ...,
    ) -> None: ...
    @classmethod
    def gpg(cls) -> str: ...

class NoBackingEncryptedFile(EncryptedFile):
    def __init__(self, cleartext: str = ...) -> None: ...
