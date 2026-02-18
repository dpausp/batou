from typing import Literal

from batou.component import Component

class Package(Component):
    package: str
    version: str | None
    check_package_is_module: bool
    timeout: int | None
    dependencies: bool
    env: dict[str, str] | None
    install_options: tuple[str, ...]

    def configure(self) -> None: ...
    @property
    def namevar_for_breadcrumb(self) -> str: ...
    def update(self) -> None: ...
    def verify(self) -> None: ...

class VirtualEnv(Component):
    version: str
    executable: str | None
    venv: VirtualEnvPyBase

    def configure(self) -> None: ...
    @property
    def python(self) -> str: ...

class VirtualEnvDownload(Component):
    version: str
    checksum: str | None
    download_url: str
    venv_cmd: str

    def configure(self) -> None: ...
    def update(self) -> None: ...
    def verify(self) -> None: ...

class VirtualEnvPy(Component):
    def update(self) -> None: ...
    def verify(self) -> None: ...

class VirtualEnvPy2_7(VirtualEnvPy):  # noqa: N801
    venv_version: str
    venv_checksum: str
    venv_options: tuple[str, ...]
    install_options: tuple[str, ...]
    pypi_url: str
    base: VirtualEnvDownload

    def configure(self) -> None: ...
    def update(self) -> None: ...
    def verify(self) -> None: ...

class VirtualEnvPyBase(Component):
    venv_version: str | None
    venv_checksum: str | None
    venv_options: tuple[str, ...]
    installer: Literal["pip", "easy_install"]
    install_options: tuple[str, ...]

    def pip_install(self, pkg: Package) -> None: ...
    def update(self) -> None: ...
    def update_pkg(self, pkg: Package) -> None: ...
    def verify(self) -> None: ...
    def verify_pkg(self, pkg: Package) -> None: ...
