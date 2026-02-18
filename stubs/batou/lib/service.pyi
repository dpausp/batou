from batou.component import Component

class Service(Component):
    executable: str
    pidfile: str | None

    def start(self) -> None: ...
