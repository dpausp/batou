from typing import Protocol

from batou.component import Component

class PlatformService(Protocol):
    """Protocol for platform-specific service operations."""

    _prepared: bool

    def start(self) -> None: ...

class Service(Component):
    """A generic component to provide a system service.

    Platform-specific components need to perform the work necessary
    to ensure startup and shutdown of the executable correctly.
    """

    executable: str
    pidfile: str | None
    _platform_component: PlatformService | None

    def start(self) -> None: ...
