from collections.abc import Iterator
from typing import Any, Literal, override
from typing import override as override_decorator

from batou.component import Component

def convert_mode(string: str) -> int: ...
def ensure_path_nonexistent(path: str) -> None: ...
def limited_buffer(
    iterator: Iterator[str],
    limit: int,
    lead: int,
    separator: str = ...,
    logdir: str = ...,
) -> tuple[list[str], bool, str]: ...

class File(Component):
    namevar: str
    ensure: Literal["file", "directory", "symlink"]
    content: str | None
    source: str
    is_template: bool
    template_context: Component | None
    template_args: dict[str, Any] | None
    encoding: str | None
    owner: str | None
    group: str | None
    mode: str | int | None
    link_to: str
    leading: bool
    sensitive_data: bool | None
    path: str
    _unmapped_path: str

    @override
    def configure(self): ...
    @override
    def last_updated(self, key: str = ...) -> float | None: ...
    @property
    @override
    def namevar_for_breadcrumb(self) -> str: ...

class BinaryFile(File):
    is_template: bool
    encoding: None
    content: bytes | None
    source: str | None

class Presence(Component):
    namevar: str
    leading: bool
    path: str

    @override
    def configure(self): ...
    @override
    def last_updated(self, key: str = ...) -> float | None: ...
    @property
    @override
    def namevar_for_breadcrumb(self) -> str: ...
    @override
    def update(self): ...
    @override
    def verify(self): ...

class SyncDirectory(Component):
    namevar: str
    source: str | None
    exclude: tuple[str, ...]
    verify_opts: str
    sync_opts: str
    path: str

    @override
    def configure(self): ...
    @property
    def exclude_arg(self) -> str: ...
    @property
    @override
    def namevar_for_breadcrumb(self) -> str: ...
    @override
    def update(self): ...
    @override
    def verify(self): ...

class Directory(Component):
    namevar: str
    leading: bool
    source: str | None
    exclude: tuple[str, ...]
    verify_opts: str | None
    sync_opts: str | None
    path: str

    @override
    def configure(self): ...
    @override
    def last_updated(self, key: str = ...) -> float: ...
    @property
    @override
    def namevar_for_breadcrumb(self) -> str: ...
    @override
    def update(self): ...
    @override
    def verify(self): ...

class FileComponent(Component):
    namevar: str
    leading: bool
    original_path: str
    path: str

    @override
    def configure(self): ...
    @property
    @override
    def namevar_for_breadcrumb(self) -> str: ...

class ManagedContentBase(FileComponent):
    content: bytes | str | None
    source: str
    sensitive_data: bool | None
    encoding: str | None
    _delayed: bool
    _max_diff: int
    _max_diff_lead: int
    _content_source_attribute: str
    diff_dir: str

    def _render(self) -> None: ...
    @override
    def configure(self) -> None: ...
    def render(self) -> None: ...
    @override
    def update(self) -> None: ...
    @override
    def verify(
        self,
        predicting: bool = ...,
        show_diff: Literal["full", "summary", "none"] = ...,
    ) -> None: ...

class Content(ManagedContentBase):
    is_template: bool
    template_context: Component | None
    template_args: dict[str, Any] | None

    @override
    def render(self): ...

class JSONContent(ManagedContentBase):
    data: Any
    override: dict[str, Any] | None
    human_readable: bool
    content_compact: str | None
    content_readable: str | None

    @override_decorator
    def render(self): ...

class YAMLContent(ManagedContentBase):
    data: Any
    override: dict[str, Any] | None

    @override_decorator
    def render(self): ...

class Owner(FileComponent):
    owner: str | int | None

    @override
    def update(self): ...
    @override
    def verify(self): ...

class Group(FileComponent):
    group: str | int | None

    @override
    def update(self): ...
    @override
    def verify(self): ...

class Mode(FileComponent):
    mode: int | str | None
    _stat: Any
    _chmod: Any

    def _select_stat_implementation(self) -> None: ...
    @override
    def configure(self) -> None: ...
    @override
    def update(self) -> None: ...
    @override
    def verify(self) -> None: ...

class Symlink(Component):
    namevar: str
    source: str | None
    target: str

    @override
    def configure(self): ...
    @override
    def update(self): ...
    @override
    def verify(self): ...

class Purge(Component):
    namevar: str
    pattern: str

    @override
    def configure(self): ...
    @override
    def update(self): ...
    @override
    def verify(self): ...
