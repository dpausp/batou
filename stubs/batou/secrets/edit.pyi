from typing import Any, Literal

from batou.environment import Environment

def main(
    editor: str,
    environment: Environment,
    edit_file: str | None = ...,
    **kw: Any,
) -> None: ...

class Editor:
    def __init__(
        self,
        editor_cmd: str,
        environment: Environment,
        edit_file: str | None = ...,
    ): ...
    def edit(self): ...
    def interact(self): ...
    def process_cmd(self, cmd: Literal["edit", "encrypt", "quit"]): ...
