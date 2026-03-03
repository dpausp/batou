import pathlib
import types

from configupdater import ConfigUpdater

debug: bool

def expect(fd: int, expected: bytes) -> tuple[bool, bytes]: ...
def get_identities() -> list[str]: ...
def get_passphrase(identity: str) -> str: ...
def get_encrypted_file(path: pathlib.Path, writeable: bool = ...) -> EncryptedFile: ...

all_encrypted_file_types: list[type[EncryptedFile]]

class EncryptedFile:
    path: pathlib.Path
    writeable: bool
    fd: object | None
    is_new: bool | None
    file_ending: str | None

    def __enter__(
        self,
    ) -> (
        AGEEncryptedFile
        | DiffableAGEEncryptedFile
        | GPGEncryptedFile
        | NoBackingEncryptedFile
    ): ...
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
    def exists(self) -> bool: ...
    @property
    def locked(self) -> bool: ...
    def write(
        self,
        content: bytes,
        recipients: list[str],
        reencrypt: bool = ...,
    ) -> None: ...
    def delete(self) -> None: ...
    def decrypt(self) -> bytes: ...

class NoBackingEncryptedFile(EncryptedFile):
    def __init__(
        self,
        path: pathlib.Path | None = ...,
        writeable: bool = ...,
    ) -> None: ...
    @property
    def locked(self) -> bool: ...
    def _lock(self) -> None: ...
    def _unlock(self) -> None: ...

class GPGEncryptedFile(EncryptedFile):
    file_ending: str
    _gpg: str | None
    GPG_BINARY_CANDIDATES: list[str]

    @classmethod
    def gpg(cls) -> str: ...

class AGEEncryptedFile(EncryptedFile):
    file_ending: str
    _age: str | None
    AGE_BINARY_CANDIDATES: list[str]

    @classmethod
    def age(cls) -> str: ...

class DiffableAGEEncryptedFile(EncryptedFile):
    file_ending: str
    _decrypted_content: ConfigUpdater | None
    _encrypted_content: ConfigUpdater | None

    def __init__(self, path: pathlib.Path, writeable: bool = ...) -> None: ...
    def decrypt_age_string(self, content: str) -> str: ...
    def encrypt_age_string(self, content: str, recipients: list[str]) -> str: ...
