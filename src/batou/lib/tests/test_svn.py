import os.path

import pytest

import batou.lib.svn
from batou.utils import cmd


@pytest.mark.slow
def test_runs_svn_to_clone_repository(root):
    repos_path = os.path.join(root.environment.workdir_base, "repos")
    cmd("svnadmin create " + repos_path)
    cmd(
        f"svn checkout file://{repos_path} upstream; cd upstream;"
        'touch foo; svn add foo; svn commit -m "bar"'
    )
    root.component += batou.lib.svn.Checkout(
        "file://" + repos_path, target="clone", revision="head"
    )
    root.component.deploy()
    assert os.path.isfile(
        os.path.join(root.environment.workdir_base, "mycomponent/clone/foo")
    )
    root.component.deploy()  # trigger verify
