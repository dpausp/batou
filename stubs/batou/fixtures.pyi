from collections.abc import Generator
from typing import Any

import pytest

from batou.component import RootComponent

@pytest.fixture
def root(tmpdir: Any) -> RootComponent: ...
@pytest.fixture(autouse=True)
def ensure_workingdir(request: Any) -> Generator[None]: ...
@pytest.fixture(autouse=True)
def reset_resolve_overrides() -> Generator[None]: ...
@pytest.fixture(autouse=True)
def output(monkeypatch: Any) -> Any: ...
