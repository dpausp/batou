from typing import Any, Literal, override

from batou.component import Component, HookComponent

class RotatedLogfile(HookComponent):
    namevar: Literal["path"]
    path: str
    key: str
    args: str
    prerotate: str | None
    postrotate: str | None

    @override
    def configure(self) -> None: ...

class Logrotate(Component):
    common_config: bytes
    logrotate_template: bytes
    logfiles: list[RotatedLogfile]
    logrotate_conf: Any

    @override
    def configure(self) -> None: ...
