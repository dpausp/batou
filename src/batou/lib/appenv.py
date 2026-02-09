import hashlib
import os.path

from batou.component import Component
from batou.lib.file import File, Symlink, ensure_path_nonexistent


class VirtualEnv(Component):
    namevar = "python_version"
    pip_version = None

    def verify(self):
        assert os.path.exists(self.parent.env_ready)
        # XXX Check if python is executable

    def update(self):
        ensure_path_nonexistent(self.parent.env_dir)
        if "__PYVENV_LAUNCHER__" in os.environ:
            del os.environ["__PYVENV_LAUNCHER__"]
        self.cmd(
            "python{{component.python_version}} -m venv {{component.parent.env_dir}}"
        )
        if self.pip_version:
            self.cmd(
                "{{component.parent.env_dir}}/bin/pip "
                f"install pip=={self.pip_version}"
            )
        else:
            self.cmd(
                "{{component.parent.env_dir}}/bin/python -m pip install --upgrade pip"
            )


class LockedRequirements(Component):
    def verify(self):
        assert os.path.exists(self.parent.env_ready)

    def update(self):
        self.python = os.path.join(self.parent.env_dir, "bin", "python")
        self.cmd(
            "{{component.python}} -m pip install --no-deps "
            "-r {{component.parent.env_dir}}/requirements.lock"
        )
        self.cmd("{{component.python}} -m pip check")


class CleanupUnused(Component):
    cleanup = ()

    def verify(self):
        if not os.path.exists(".appenv/"):
            return
        protected = set([self.parent.env_hash, self.parent.last_env_hash, "current"])
        self.cleanup = set(os.listdir(".appenv/")) - protected
        assert not self.cleanup

    def update(self):
        for path in self.cleanup:
            ensure_path_nonexistent(os.path.join(".appenv", path))


class AppEnv(Component):
    """Manage a Python-package based application installation.

    This uses virtualenv and pip with a "lockfile" style requirements.txt
    file.

    Place a file name "requirements.lock" in the defdir and specify the version
    of Python 3 to be used.

    Will automatically rebuild based on hashing of the AppEnv code,
    the requirements file and the chosen version of Python.

    The result is a light-weight 'pseudo' virtualenv with a bin/ directory
    symlinked to the real virtualenv used under the hood.

    """

    namevar = "python_version"
    pip_version = None

    def configure(self):
        with open("requirements.lock", "r") as f:
            lockfile = f.read()

        # Include editable package sources in hash so code changes trigger rebuild
        import re

        editable_sources = []
        for line in lockfile.splitlines():
            match = re.match(r"^-e\s+(.+)$", line.strip())
            if match:
                path = match.group(1).strip()
                # Resolve relative path
                if not os.path.isabs(path):
                    path = os.path.join(self.workdir, path)
                if os.path.exists(path):
                    editable_sources.append(path)

        # Read appenv code
        with open(__file__, "r") as f:
            hash_content = lockfile + self.python_version + f.read()

        # Read editable source files
        for source_path in editable_sources:
            for root, dirs, files in os.walk(source_path):
                for filename in files:
                    filepath = os.path.join(root, filename)
                    if (
                        filepath.endswith(".pyc")
                        or ".git" in filepath
                        or ".hg" in filepath
                    ):
                        continue
                    try:
                        with open(filepath, "r", errors="ignore") as f:
                            hash_content += f.read()
                    except (IOError, UnicodeDecodeError):
                        pass

        hash_content = hash_content.encode("utf-8")
        self.env_hash = hashlib.new("sha256", hash_content).hexdigest()[:8]
        self.env_dir = os.path.join(".appenv", self.env_hash)
        self.env_ready = os.path.join(self.env_dir, "appenv.ready")

        self += VirtualEnv(self.python_version, pip_version=self.pip_version)
        self += File(os.path.join(self.env_dir, "requirements.lock"), content=lockfile)
        self += LockedRequirements()

        # If we got here, then we can place the ready marker
        self += File(
            os.path.join(self.env_dir, "appenv.ready"),
            content="Ready or not, here I come, you can't hide\n",
        )

        # Save current to skip it in cleanup
        self.last_env_hash = None
        if os.path.exists(os.path.join(self.workdir, ".appenv/current")):
            self.last_env_hash = os.path.basename(
                os.readlink(os.path.join(self.workdir, ".appenv/current"))
            )

        # Shim
        self += Symlink(".appenv/current", source=self.env_dir)
        for p in ["bin", "lib", "pyvenv.cfg"]:
            self += Symlink(p, source=".appenv/current/" + p)

        self += CleanupUnused()

    @property
    def namevar_for_breadcrumb(self):
        return self.env_hash[:8]
