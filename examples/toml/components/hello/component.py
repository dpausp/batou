"""Example component for TOML showcase."""

from batou.component import Component
from batou.lib.file import File


class Hello(Component):
    """A simple hello world component."""

    def configure(self):
        self += File("hello.txt", content="Hello from TOML example!\n")
