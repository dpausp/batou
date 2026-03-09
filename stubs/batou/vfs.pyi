from typing import Protocol

from batou.environment import ConfigSection, Environment

class _PathMapper(Protocol):
    """Protocol for path mapping operations."""

    def map(self, path: str) -> str: ...

type PathMapper = _PathMapper

class Map:
    """VFS mapper that replaces path prefixes based on configuration."""

    _map: list[tuple[str, str]]

    def __init__(self, environment: Environment, config: ConfigSection | None): ...
    def map(self, path: str) -> str: ...

class Developer:
    """VFS mapper for development environments, creates sandboxed paths."""

    environment: Environment

    def __init__(self, environment: Environment, config: ConfigSection | None): ...
    def map(self, path: str) -> str: ...
