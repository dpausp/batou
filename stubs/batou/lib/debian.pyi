from typing import override

import batou.lib.logrotate
import batou.lib.supervisor
from batou.component import Component

class RebootCronjob(Component):
    @override
    def configure(self) -> None: ...

class Supervisor(batou.lib.supervisor.Supervisor):
    pidfile: str

class Logrotate(batou.lib.logrotate.Logrotate):
    common_config: bytes

class LogrotateCronjob(Component):
    directory: str

    @override
    def configure(self) -> None: ...
