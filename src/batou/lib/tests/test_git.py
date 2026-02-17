import os.path

import pytest

import batou.lib.git
from batou.utils import cmd


def _repos_path(root, name):
    repos_path = os.path.join(root.environment.workdir_base, name)
    cmd(
        f"mkdir {repos_path}; cd {repos_path}; git init;"
        "git config user.name Jenkins;"
        "git config user.email jenkins@example.com;"
        "touch foo; git add .;"
        'git commit -am "foo"'
    )
    return repos_path


@pytest.fixture(scope="function")
def repos_path(root, name="upstream"):
    return _repos_path(root, name)


@pytest.fixture(scope="function")
def repos_path2(root, name="upstream2"):
    return _repos_path(root, name)


@pytest.mark.slow
def test_runs_git_to_clone_repository(root, repos_path, git_main_branch):
    root.component += batou.lib.git.Clone(
        repos_path, target="clone", branch=git_main_branch
    )
    root.component.deploy()
    assert os.path.isfile(
        os.path.join(root.environment.workdir_base, "mycomponent/clone/foo")
    )
    root.component.deploy()  # trigger verify


@pytest.mark.slow
def test_directly_after_clone_nothing_is_merged(root, repos_path):
    # When a Clone is confirgured with a branch, the general gesture for
    # updating is "git merge origin/branch", but directly after cloning, the
    # Clone is still on master, so this would try to merge the configured
    # branch into master, which is wrong.
    cmd(
        f"cd {repos_path}; git checkout -b other; touch bar; echo qux > foo;"
        'git add .; git commit -am "other";'
        # Set up branches to be different, so we see that no merge takes place
        "git checkout master; "
        'echo one > foo; git add . ; git commit -am "foo master";'
    )
    root.component += batou.lib.git.Clone(repos_path, target="clone", branch="other")
    root.component.deploy()
    assert os.path.isfile(
        os.path.join(root.environment.workdir_base, "mycomponent/clone/bar")
    )


@pytest.mark.slow
def test_setting_branch_updates_on_incoming_changes(root, repos_path, git_main_branch):
    root.component += batou.lib.git.Clone(
        repos_path, target="clone", branch=git_main_branch
    )
    root.component.deploy()
    cmd(f'cd {repos_path}; touch bar; git add .; git commit -m "commit"')
    root.component.deploy()
    assert os.path.isfile(
        os.path.join(root.environment.workdir_base, "mycomponent/clone/bar")
    )


@pytest.mark.slow
def test_setting_revision_updates_on_incoming_changes(root, repos_path):
    cmd(
        f'cd {repos_path}; touch bar; git add .; git commit -m "commit2"'
    )
    commit1, _ = cmd(f"cd {repos_path}; git rev-parse HEAD^")
    root.component += batou.lib.git.Clone(repos_path, target="clone", revision=commit1)
    root.component.deploy()
    cmd(
        f'cd {repos_path}; touch qux; git add .; git commit -m "commit3"'
    )
    root.component.deploy()  # Our main assertion: Nothing breaks here
    assert not os.path.isfile(
        os.path.join(root.environment.workdir_base, "mycomponent/clone/qux")
    )


@pytest.mark.slow
def test_branch_does_switch_branch(root, repos_path):
    cmd(
        f"cd {repos_path}; touch bar; git add .; git checkout -b bar;"
        'git commit -m "commit branch"'
    )
    root.component += batou.lib.git.Clone(repos_path, target="clone", branch="bar")
    root.component.deploy()
    stdout, stderr = cmd(
        f"cd {root.workdir}/clone; git rev-parse --abbrev-ref HEAD"
    )
    assert "bar" == stdout.strip()


@pytest.mark.slow
def test_tag_does_switch_tag(root, repos_path):
    cmd(f"""cd {repos_path}; git tag -a v1.0 -m "version 1.0" """)
    cmd(
        f'cd {repos_path}; touch bar; git add .;git commit -m "commit branch"'
    )
    cmd(f"""cd {repos_path}; git tag -a v1.1 -m "version 1.1" """)

    for tag in ("v1.0", "v1.1"):
        root.component += batou.lib.git.Clone(repos_path, target="clone", tag=tag)
        root.component.deploy()
        stdout, stderr = cmd(
            f"cd {root.workdir}/clone; git describe --tags"
        )
        assert tag == stdout.strip()


@pytest.mark.slow
def test_has_changes_counts_changes_to_tracked_files(root, repos_path, git_main_branch):
    clone = batou.lib.git.Clone(repos_path, target="clone", branch=git_main_branch)
    root.component += clone
    root.component.deploy()
    assert not clone.has_changes()
    cmd(f"touch {root.workdir}/clone/bar")
    cmd(f"cd {root.workdir}/clone; git add bar")
    assert clone.has_changes()


@pytest.mark.slow
def test_has_changes_counts_untracked_files_as_changes(
    root, repos_path, git_main_branch
):
    clone = batou.lib.git.Clone(repos_path, target="clone", branch=git_main_branch)
    root.component += clone
    root.component.deploy()
    assert not clone.has_changes()
    cmd(f"touch {root.workdir}/clone/bar")
    assert clone.has_changes()


@pytest.mark.slow
def test_clean_clone_updates_on_incoming_changes(root, repos_path, git_main_branch):
    root.component += batou.lib.git.Clone(
        repos_path,
        target="clone",
        branch=git_main_branch,
    )
    root.component.deploy()
    cmd(f'cd {repos_path}; touch bar; git add .; git commit -m "commit"')
    root.component.deploy()
    assert os.path.isfile(root.component.map("clone/bar"))


@pytest.mark.slow
def test_no_clobber_changes_protected_on_update_with_incoming(
    root, repos_path, git_main_branch
):
    root.component += batou.lib.git.Clone(
        repos_path, target="clone", branch=git_main_branch
    )
    root.component.deploy()
    cmd(f'cd {repos_path}; touch bar; git add .; git commit -m "commit"')
    cmd(f"cd {root.workdir}/clone; echo foobar >foo")
    with pytest.raises(RuntimeError) as e:
        root.component.deploy()
    assert e.value.args[0] == "Refusing to clobber dirty work directory."
    with open(root.component.map("clone/foo")) as f:
        assert f.read() == "foobar\n"


@pytest.mark.slow
def test_no_clobber_changes_protected_on_update_without_incoming(
    root, repos_path, git_main_branch
):
    root.component += batou.lib.git.Clone(
        repos_path, target="clone", branch=git_main_branch
    )
    root.component.deploy()
    cmd(f"cd {root.workdir}/clone; echo foobar >foo")
    with pytest.raises(RuntimeError) as e:
        root.component.deploy()
    assert e.value.args[0] == "Refusing to clobber dirty work directory."
    with open(root.component.map("clone/foo")) as f:
        assert f.read() == "foobar\n"


@pytest.mark.slow
def test_no_clobber_untracked_files_are_kept_on_update(
    root, repos_path, git_main_branch
):
    root.component += batou.lib.git.Clone(
        repos_path, target="clone", branch=git_main_branch
    )
    root.component.deploy()
    cmd(f"cd {root.workdir}/clone; mkdir bar; echo foobar >bar/baz")
    with pytest.raises(RuntimeError) as e:
        root.component.deploy()
    assert e.value.args[0] == "Refusing to clobber dirty work directory."
    with open(root.component.map("clone/bar/baz")) as f:
        assert f.read() == "foobar\n"


@pytest.mark.slow
def test_clobber_changes_lost_on_update_with_incoming(
    root, repos_path, git_main_branch
):
    root.component += batou.lib.git.Clone(
        repos_path, target="clone", branch=git_main_branch, clobber=True
    )
    root.component.deploy()
    cmd(f'cd {repos_path}; touch bar; git add .; git commit -m "commit"')
    cmd(f"cd {root.workdir}/clone; echo foobar >foo")
    root.component.deploy()
    assert os.path.exists(root.component.map("clone/bar"))
    with open(root.component.map("clone/foo")) as f:
        assert not f.read()


@pytest.mark.slow
def test_clobber_changes_lost_on_update_without_incoming(
    root, repos_path, git_main_branch
):
    root.component += batou.lib.git.Clone(
        repos_path, target="clone", branch=git_main_branch, clobber=True
    )
    root.component.deploy()
    cmd(f"cd {root.workdir}/clone; echo foobar >foo")
    root.component.deploy()
    with open(root.component.map("clone/foo")) as f:
        assert not f.read()


@pytest.mark.slow
def test_clobber_untracked_files_are_removed_on_update(
    root, repos_path, git_main_branch
):
    root.component += batou.lib.git.Clone(
        repos_path, target="clone", branch=git_main_branch, clobber=True
    )
    root.component.deploy()
    cmd(f"cd {root.workdir}/clone; mkdir bar; echo foobar >bar/baz")
    root.component.deploy()
    assert not os.path.exists(root.component.map("clone/bar/baz"))


@pytest.mark.slow
def test_clean_clone_vcs_update_false_leaves_changes_intact(
    root, repos_path, git_main_branch
):
    root.component += batou.lib.git.Clone(
        repos_path, target="clone", branch=git_main_branch, vcs_update=False
    )
    root.component.deploy()
    cmd(
        f"cd {repos_path}; echo foobar >foo; touch bar; git add .; "
        'git commit -m "commit"'
    )
    cmd(f"cd {root.workdir}/clone; echo asdf >foo")
    root.component.deploy()
    with open(root.component.map("clone/foo")) as f:
        assert "asdf\n" == f.read()
    assert not os.path.exists(root.component.map("clone/bar"))


@pytest.mark.slow
def test_changed_remote_is_updated(root, repos_path, repos_path2, git_main_branch):
    git = batou.lib.git.Clone(repos_path, target="clone", branch=git_main_branch)
    root.component += git

    # Fresh, unrelated repo
    cmd(
        f'cd {repos_path2}; echo baz >bar; git add .;git commit -m "commit"'
    )

    root.component.deploy()
    assert not os.path.exists(root.component.map("clone/bar"))
    git.url = repos_path2
    root.component.deploy()
    assert os.path.exists(root.component.map("clone/bar"))


@pytest.mark.slow
def test_clone_into_workdir_works(root, repos_path, repos_path2, git_main_branch):
    git = batou.lib.git.Clone(repos_path, branch=git_main_branch)
    with open(root.component.map("asdf"), "w") as f:
        f.write("foo")
    root.component += git
    root.component.deploy()
    assert not os.path.exists(root.component.map("asdf"))


@pytest.mark.slow
def test_can_read_untracked_files_correctly(root, repos_path, git_main_branch):
    fun_strings = [
        "this string has spaces in it",
        "this string has a ' in it",
        'this string has a " in it',
        '"this string has a \' and a " in it"',
        "this string has a \\ in it",
        "this string has a \\ and a ' in it",
        "this string has a \\ and a & in it",
    ]
    git = batou.lib.git.Clone(repos_path, branch=git_main_branch)
    root.component += git
    root.component.deploy()
    for s in fun_strings:
        with open(root.component.map(s), "w") as f:
            f.write(s)
    with git.chdir(git.target):
        assert set(git.untracked_files()) == set(fun_strings)
