from typing import Literal, override

from batou.component import Component

class Checkout(Component):
    namevar: Literal["url"]
    url: str
    target: str
    revision: str | None

    @override
    def configure(self) -> None: ...
    @override
    def update(self) -> None: ...
    @override
    def verify(self) -> None: ...

Subversion = Checkout  # BBB
