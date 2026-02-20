import os
import sys

import pytest

from batou.environment import Environment
from batou.secrets.edit import Editor


def test_edit_gpg(tmpdir):
    editor = Editor(
        "true",
        environment=Environment("tutorial", basedir="examples/tutorial-secrets"),
        edit_file="asdf",
    )
    editor.cleartext = "asdf"
    editor.edit()
    assert editor.cleartext == "asdf"


@pytest.mark.skipif(
    sys.version_info < (3, 7),
    reason="age is available in tests with python 3.7 only",
)
def test_edit_age(tmpdir):
    editor = Editor(
        "true",
        environment=Environment("age", basedir="examples/tutorial-secrets"),
        edit_file="asdf",
    )
    editor.cleartext = "asdf"
    editor.edit()
    assert editor.cleartext == "asdf"


def test_edit_command_loop(tmpdir, capsys, patterns):
    editor = Editor(
        "true",
        environment=Environment("tutorial", basedir="examples/tutorial-secrets"),
    )
    editor.cleartext = "asdf"

    with pytest.raises(ValueError):
        editor.process_cmd("asdf")

    def broken_cmd():
        raise RuntimeError("gpg is broken")

    editor.edit = broken_cmd
    editor.encrypt = broken_cmd

    cmds = ["edit", "asdf", "encrypt", "quit"]

    def _input():
        return cmds.pop(0)

    editor._input = _input
    editor.interact()

    out, err = capsys.readouterr()
    assert err == ""

    # Traceback content is variable (line numbers, file paths, f-string vs .format())
    patterns.traceback_lines.optional(
        """\
Traceback (most recent call last):
  File ".../src/batou/secrets/edit.py", line ..., in interact
    self.process_cmd(cmd)
    ~~~~~~~~~~~~~~~~^^^^^
  File ".../src/batou/secrets/edit.py", line ..., in process_cmd
    self.edit()
    ~~~~~~~~~^^
  File ".../src/batou/secrets/tests/test_editor.py", line ..., in broken_cmd
    raise RuntimeError("gpg is broken")
RuntimeError: gpg is broken"""
    )

    patterns.traceback_asdf.optional(
        """\
Traceback (most recent call last):
  File ".../src/batou/secrets/edit.py", line ..., in interact
    self.process_cmd(cmd)
    ~~~~~~~~~~~~~~~~^^^^^
  File ".../src/batou/secrets/edit.py", line ..., in process_cmd
    raise ValueError...
ValueError: unknown command `asdf`"""
    )

    patterns.traceback_encrypt.optional(
        """\
Traceback (most recent call last):
  File ".../src/batou/secrets/edit.py", line ..., in interact
    self.process_cmd(cmd)
    ~~~~~~~~~~~~~~~~^^^^^
  File ".../src/batou/secrets/edit.py", line ..., in process_cmd
    self.encrypt()
    ~~~~~~~~~~~~^^
  File ".../src/batou/secrets/tests/test_editor.py", line ..., in broken_cmd
    raise RuntimeError("gpg is broken")
RuntimeError: gpg is broken"""
    )

    patterns.empty_lines.optional("<empty-line>")

    patterns.output.merge(
        "traceback_lines", "traceback_asdf", "traceback_encrypt", "empty_lines"
    )
    patterns.output.in_order(
        """\
<empty-line>
An error occurred: gpg is broken
Traceback:
<empty-line>
Your changes are still available. You can try:
...edit...-- opens editor with current data again
...encrypt...-- tries to encrypt current data again
...quit...-- quits and loses your changes
<empty-line>
An error occurred: gpg is broken
Traceback:
<empty-line>
Your changes are still available. You can try:
...edit...-- opens editor with current data again
...encrypt...-- tries to encrypt current data again
...quit...-- quits and loses your changes
<empty-line>
An error occurred: unknown command `asdf`
Traceback:
<empty-line>
Your changes are still available. You can try:
...edit...-- opens editor with current data again
...encrypt...-- tries to encrypt current data again
...quit...-- quits and loses your changes
<empty-line>
An error occurred: gpg is broken
Traceback:
<empty-line>
Your changes are still available. You can try:
...edit...-- opens editor with current data again
...encrypt...-- tries to encrypt current data again
...quit...-- quits and loses your changes
"""
    )

    assert patterns.output == out


def test_edit_file_has_secret_prefix_gpg(tmpdir, encrypted_file):
    filename = "asdf123"
    editor = Editor(
        "true",
        environment=Environment("tutorial", basedir="examples/tutorial-secrets"),
        edit_file=filename,
    )
    assert editor.file.path.name == f"secret-{filename}.gpg"


@pytest.mark.skipif(
    sys.version_info < (3, 7),
    reason="age is available in tests with python 3.7 only",
)
def test_edit_file_has_secret_prefix_age(tmpdir, encrypted_file):
    filename = "asdf123"
    editor = Editor(
        "true",
        environment=Environment("age", basedir="examples/tutorial-secrets"),
        edit_file=filename,
    )
    assert editor.file.path.name == f"secret-{filename}.age"


def test_blank_edit(tmpdir, encrypted_file):
    editor = Editor(
        "true",
        environment=Environment("tutorial", basedir="examples/tutorial-secrets"),
        edit_file="asdf",
    )
    with editor.file:
        editor.original_cleartext = None
        editor.cleartext = ""
        editor.edit()
        assert editor.cleartext == ""
        editor.encrypt()
    with open(editor.file.path, "rb") as f:
        assert f.read() != b""
    os.unlink(editor.file.path)
