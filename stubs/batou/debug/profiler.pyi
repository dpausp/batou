from collections.abc import Iterable
from typing import Any

from batou.debug.settings import DebugSettings
from batou.host import Host

class Profiler:
    enabled: bool

    def __init__(self, debug_settings: DebugSettings): ...
    def generate_reports(self, hosts: Iterable[Host]): ...
