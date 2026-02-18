from typing import Any

from batou.component import Component, HookComponent

class RotatedLogfile(HookComponent):
    path: str
    key: str
    args: str
    prerotate: str | None
    postrotate: str | None

    def configure(self) -> None: ...

class Logrotate(Component):
    common_config: bytes
    logrotate_template: bytes
    logfiles: list[RotatedLogfile]
    logrotate_conf: Any

    def configure(self) -> None: ...
