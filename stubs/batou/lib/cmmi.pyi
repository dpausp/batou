from typing import Any, Literal, override

from batou.component import Component

class Configure(Component):
    namevar: Literal["path"]
    path: str
    args: str
    prefix: str | None
    build_environment: dict[str, Any] | None

    @override
    def configure(self) -> None: ...
    @override
    def update(self) -> None: ...
    @override
    def verify(self) -> None: ...

class Make(Component):
    namevar: Literal["path"]
    path: str
    build_environment: dict[str, Any] | None

    @override
    def update(self) -> None: ...
    @override
    def verify(self) -> None: ...

class Build(Component):
    namevar: Literal["uri"]
    uri: str
    checksum: str | None
    configure_args: str
    prefix: str | None
    build_environment: dict[str, Any] | None

    @override
    def configure(self) -> None: ...
    @property
    @override
    def namevar_for_breadcrumb(self) -> str: ...
