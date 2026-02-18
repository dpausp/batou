import types
from collections.abc import Iterator
from typing import Any, Self

from batou.component import Component

class DMGExtractor(Component):
    archive: str
    target: str | None
    create_target_dir: bool
    strip: int
    volume: "DMGVolume"
    _supports_strip: bool

    def __enter__(self) -> Self: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        tb: types.TracebackType | None,
    ) -> None: ...
    def get_names_from_archive(self) -> list[str]: ...
    def update(self) -> None: ...

class DMGVolume:
    path: str
    name: str
    volume_path: str | None

    def __init__(self, path: str) -> None: ...
    def _mount(self) -> str: ...
    def _unmount(self) -> None: ...
    def copy_to(self, target_dir: str) -> None: ...
    def namelist(self) -> list[Any]: ...

class Extract(Component):
    archive: str
    create_target_dir: bool
    target: str | None
    strip: int
    extractor: "Extractor"

    def configure(self) -> None: ...
    @property
    def namevar_for_breadcrumb(self) -> str: ...

class Extractor(Component):
    archive: str
    target: str | None
    create_target_dir: bool
    strip: int
    _supports_strip: bool
    suffixes: tuple[str, ...]

    @classmethod
    def can_handle(cls, archive: str) -> bool: ...
    def configure(self) -> None: ...
    @classmethod
    def extract_base_name(cls, archive: str) -> str | None: ...
    def get_names_from_archive(self) -> list[str]: ...
    @property
    def namevar_for_breadcrumb(self) -> str: ...
    def verify(self) -> None: ...

class Untar(Extractor):
    exclude: tuple[str, ...] | str
    _supports_strip: bool

    def configure(self) -> None: ...
    def get_names_from_archive(self) -> list[str]: ...
    def update(self) -> None: ...

class Unzip(Extractor):
    def get_names_from_archive(self) -> list[str]: ...
    def update(self) -> None: ...
