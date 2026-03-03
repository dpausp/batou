import sys

from batou.component import Component
from batou.lib.python import VirtualEnv


def test_venv_creates_correct_python_version(root):
    """Test that VirtualEnv creates a venv with the requested Python version."""
    import ast

    class Playground(Component):
        namevar = "version"

        def configure(self):
            self.venv = VirtualEnv(self.version)
            self += self.venv

    # Use current Python version (e.g., "3.14")
    version = f"{sys.version_info.major}.{sys.version_info.minor}"
    playground = Playground(version)
    root.component += playground
    playground.deploy()

    # Verify the venv was created with correct Python version
    out, _ = playground.cmd(
        f'{playground.workdir}/bin/python -c "import sys; print(sys.version_info[:2])"'
    )
    assert (sys.version_info.major, sys.version_info.minor) == ast.literal_eval(out)


def test_venv_does_not_update_if_python_does_not_change(root):
    """Test that VirtualEnv is idempotent when Python version stays the same."""

    class Playground(Component):
        namevar = "version"

        def configure(self):
            self.venv = VirtualEnv(self.version)
            self += self.venv

    # Use current Python version (e.g., "3.14")
    version = f"{sys.version_info.major}.{sys.version_info.minor}"
    playground = Playground(version)
    root.component += playground
    playground.deploy()
    assert playground.changed

    # Deploy again with same version - should not change
    playground.deploy()
    assert not playground.changed
