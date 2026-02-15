from batou.component import Component

class DPKG(Component):
    namevar: str = "package"

    def verify(self) -> None: ...
    def update(self) -> None: ...
