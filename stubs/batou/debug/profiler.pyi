from typing import Any

from batou.debug.settings import DebugSettings

class Profiler:
    enabled: bool

    def __init__(self, debug_settings: DebugSettings): ...
    def generate_reports(self, hosts: list[Any]): ...
