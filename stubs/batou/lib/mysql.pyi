from typing import Any, Literal

from batou.component import Component

USE_SUDO: Any

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

    def configure(self) -> None: ...
    def _mysql(self, cmd: str) -> tuple[str, str]: ...
    def verify(self) -> None: ...
    def update(self) -> None: ...
    @property
    def namevar_for_breadcrumb(self) -> str: ...

class Database(Component):
    namevar: Literal["database"]
    database: str
    charset: str
    base_import_file: str | None
    admin_password: str | Any | None

    def configure(self) -> None: ...

class User(Component):
    namevar: Literal["user"]
    password: str | None
    allow_from_hostname: str
    admin_password: str | Any | None
    SET_PASSWORD_QUERY: str

    def configure(self) -> None: ...

class Grant(Command):
    namevar: Literal["grant_db"]
    user: str
    allow_from_hostname: str
    statement: str
