import os
import shutil
from pathlib import Path

import pytest

# Path to examples directory (relative to this test file)
EXAMPLES_DIR = Path(__file__).parent.parent.parent.parent / "examples"
# Path to batou repo root (for adjusting pyproject.toml paths)
BATOU_ROOT = Path(__file__).parent.parent.parent.parent


@pytest.fixture
def isolated_example(tmp_path, monkeypatch):
    """Copy an example directory to a temp location for isolated testing.

    Adjusts pyproject.toml to point to the correct batou source path.
    Prevents race conditions when running tests in parallel with tox.

    Usage:
        def test_foo(isolated_example):
            isolated_example("errors")
            out, _ = cmd("./batou deploy errors")
    """

    def _copy(example_name: str) -> Path:
        src = EXAMPLES_DIR / example_name
        dst = tmp_path / example_name
        shutil.copytree(src, dst)

        # Adjust batou path in pyproject.toml if it exists
        pyproject = dst / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text()
            # Replace relative path with absolute path to batou root
            content = content.replace('path = "../../"', f'path = "{BATOU_ROOT}"')
            pyproject.write_text(content)

        monkeypatch.chdir(dst)
        return dst

    return _copy


@pytest.fixture()
def sample_service(tmpdir):
    shutil.copytree(
        os.path.dirname(__file__) + "/fixture/sample_service",
        str(tmpdir / "sample_service"),
    )
    target = str(tmpdir / "sample_service")
    os.chdir(target)
    return target


@pytest.fixture(autouse=True)
def ensure_git_config(monkeypatch):
    monkeypatch.setitem(os.environ, "GIT_AUTHOR_EMAIL", "test@example.com")
    monkeypatch.setitem(os.environ, "GIT_AUTHOR_NAME", "Mr. U. Test")
    monkeypatch.setitem(os.environ, "GIT_COMMITTER_EMAIL", "test@example.com")
    monkeypatch.setitem(os.environ, "GIT_COMMITTER_NAME", "Mr. U. Test")
