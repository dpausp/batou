from typing import Any, Final, Literal, override

from batou.component import Component

USE_SUDO: Final[bool]

class Command(Component):
    namevar: Literal["statement"]
    admin_password: str | Any
    admin_user: str
    hostname: str | None
    port: int | None
    db: str
    unless: str
    statement: str
    tmp: str

    @override
    def configure(self) -> None: ...
    def _mysql(self, cmd: str) -> tuple[str, str]: ...
    @override
    def verify(self) -> None: ...
    @override
    def update(self) -> None: ...
    @property
    @override
    def namevar_for_breadcrumb(self) -> str: ...

class Database(Component):
    namevar: Literal["database"]
    database: str
    charset: str
    base_import_file: str | None
    admin_password: str | Any | None

    @override
    def configure(self) -> None: ...

class User(Component):
    namevar: Literal["user"]
    password: str | None
    allow_from_hostname: str
    admin_password: str | Any | None
    SET_PASSWORD_QUERY: Final[str]

    @override
    def configure(self) -> None: ...

class Grant(Command):
    namevar: Literal["grant_db"]
    user: str
    allow_from_hostname: str
    statement: str
