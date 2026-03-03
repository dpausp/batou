from typing import Literal

from batou.component import Component

class DPKG(Component):
    namevar: Literal["package"]

    def verify(self) -> None: ...
    def update(self) -> None: ...
