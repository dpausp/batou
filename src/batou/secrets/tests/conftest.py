import pathlib
import shutil

import pytest

FIXTURE = pathlib.Path(__file__).parent / "fixture"
FIXTURE_ENCRYPTED_CONFIG = FIXTURE / "encrypted.cfg.gpg"


@pytest.fixture(scope="function")
def encrypted_file(tmpdir):
    """Provide a temporary copy of the encrypted config."""
    return pathlib.Path(shutil.copy(FIXTURE_ENCRYPTED_CONFIG, tmpdir))


@pytest.fixture(scope="session", autouse=True)
def cleanup_gpg_sockets():
    yield
    for path in [
        "S.dirmngr",
        "S.gpg-agent",
        "S.gpg-agent.browser",
        "S.gpg-agent.extra",
        "S.gpg-agent.ssh",
    ]:
        try:
            (FIXTURE / "gnupg" / path).unlink()
        except OSError:
            pass
