from typing import Any

from batou.component import Component, HookComponent

class CronJob(HookComponent):
    command: str
    key: str
    args: str
    timing: str | None
    logger: str | None

    def format(self) -> str: ...

class CronTab(Component):
    crontab_template: str
    mailto: str | None
    purge: bool
    env: dict[str, Any]
    jobs: list[CronJob] | None
    crontab: Any

    def configure(self) -> None: ...

class PurgeCronTab(Component):
    def configure(self) -> None: ...

class InstallCrontab(Component):
    crontab: Any

    def configure(self) -> None: ...
    def verify(self) -> None: ...
    def update(self) -> None: ...
