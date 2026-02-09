import os.path
import subprocess
import tempfile

import pytest

import batou.utils


@pytest.fixture(autouse=True)
def ensure_gpg_homedir(monkeypatch):
    home = os.path.join(
        os.path.dirname(__file__), "secrets", "tests", "fixture", "gnupg"
    )
    monkeypatch.setitem(os.environ, "GNUPGHOME", home)


@pytest.fixture(autouse=True)
def ensure_age_identity(monkeypatch):
    key = os.path.join(
        os.path.dirname(__file__),
        "secrets",
        "tests",
        "fixture",
        "age",
        "id_ed25519",
    )
    monkeypatch.setitem(os.environ, "BATOU_AGE_IDENTITIES", key)


@pytest.fixture(autouse=True)
def reset_address_defaults():
    v4, v6 = batou.utils.Address.require_v4, batou.utils.Address.require_v6
    yield
    batou.utils.Address.require_v4, batou.utils.Address.require_v6 = v4, v6


@pytest.fixture(scope="session")
def git_main_branch() -> str:
    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.check_call(["git", "-C", tmpdir, "init", "."])
        return (
            subprocess.check_output(["git", "-C", tmpdir, "branch", "--show-current"])
            .decode("ascii")
            .strip()
        )


@pytest.fixture(scope="function", autouse=True)
def cleanup_fd_tracking():
    """Clean up FD tracking singleton after each test to prevent hook leakage.

    This is critical because:
    1. FileDescriptorTracker is a singleton that persists across tests
    2. The tracker wraps builtins.open with a hook
    3. The hook's close_hook wrapper creates reference cycles
    4. These cycles prevent proper garbage collection
    5. This causes ResourceWarnings in later tests
    """
    from batou.debug.fd_tracker import FileDescriptorTracker
    import warnings
    import pytest

    # Suppress unraisable exception warnings during test execution
    # These are often false positives from coverage/pytest internals
    warnings.filterwarnings("ignore", category=pytest.PytestUnraisableExceptionWarning)

    yield

    FileDescriptorTracker.cleanup()
