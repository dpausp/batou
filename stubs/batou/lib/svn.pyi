from typing import Literal

from batou.component import Component

class Checkout(Component):
    namevar: Literal["url"]
    url: str
    target: str
    revision: str | None

    def configure(self) -> None: ...
    def update(self) -> None: ...
    def verify(self) -> None: ...

Subversion = Checkout  # BBB
