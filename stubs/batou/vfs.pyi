from batou.environment import (
    ConfigSection,
    Environment,
)
from typing import Optional


class Developer:
    def __init__(self, environment: Environment, config: Optional[ConfigSection]): ...
    def map(self, path: str) -> str: ...
