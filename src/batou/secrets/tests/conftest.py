import pathlib
import shutil

import pytest

FIXTURE = pathlib.Path(__file__).parent / "fixture"
FIXTURE_ENCRYPTED_CONFIG = FIXTURE / "encrypted.cfg.gpg"
FIXTURE_AGE_IDENTITY = FIXTURE / "age" / "id_ed25519"


@pytest.fixture(scope="function")
def encrypted_file(tmpdir):
    """Provide a temporary copy of the encrypted config."""
    return pathlib.Path(shutil.copy(FIXTURE_ENCRYPTED_CONFIG, tmpdir))


@pytest.fixture(scope="function")
def age_encrypted_file(tmpdir, monkeypatch):
    """Provide a temporary file for AGE encryption tests.

    Creates a properly formatted AGE-diffable config file where values
    are base64-encoded AGE-encrypted strings.
    """
    # Set up AGE identity for decryption
    monkeypatch.setenv("BATOU_AGE_IDENTITIES", str(FIXTURE_AGE_IDENTITY))

    # Reset the cached identities so they get reloaded with our env var
    from batou.secrets.encryption import pyrage_encryption

    pyrage_encryption.identities = None

    # Create the AGE-diffable config file
    dest = pathlib.Path(tmpdir) / "encrypted.cfg.age"

    # Read the public key
    public_key = (FIXTURE / "age" / "id_ed25519.pub").read_text().strip()

    # Encrypt the value using age CLI
    import subprocess

    cleartext_value = b"old value"
    result = subprocess.run(
        ["age", "-r", public_key],
        input=cleartext_value,
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"age encryption failed: {result.stderr.decode()}")

    # Base64 encode the encrypted value
    import base64

    encrypted_b64 = base64.b64encode(result.stdout).decode("utf-8")

    # Create the config file in AGE-diffable format
    config_content = f"""[batou]
members = {public_key}

[asdf]
value = {encrypted_b64}
"""
    dest.write_text(config_content)
    return dest


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
