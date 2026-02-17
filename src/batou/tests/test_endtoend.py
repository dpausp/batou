import os
import os.path
import shutil

from batou.environment import Environment
from batou.tests.ellipsis import Ellipsis
from batou.utils import cmd


def test_service_early_resource():
    env = Environment(
        "dev",
        basedir=os.path.dirname(__file__) + "/fixture/service_early_resource",
    )
    env.load()
    env.configure()
    assert env.resources.get("zeo") == ["127.0.0.1:9000"]


def test_example_errors_early():
    os.chdir("examples/errors")
    out, _ = cmd("./batou deploy errors", acceptable_returncodes=[1])
    assert out == Ellipsis(
        """\
batou/2... (cpython 3...)
No expert/debug flags enabled
Use `batou debug` command to see all available debug settings
... Preparing ...
📦 main: Loading environment `errors`...
🔍 main: Verifying repository ...
🔑 main: Loading secrets ...

ERROR: Failed loading component file
           File: .../examples/errors/components/component5/component.py
      Exception: invalid syntax (component.py, line 1)
Traceback (simplified, most recent call last):
<no-non-remote-internal-traceback-lines-found>

ERROR: Failed loading component file
           File: .../examples/errors/components/component6/component.py
      Exception: No module named 'asdf'
Traceback (simplified, most recent call last):
  File ".../errors/components/component6/component.py", line 1, in <module>
    import asdf  # noqa: F401 import unused
...
ERROR: Missing component
      Component: missingcomponent

ERROR: Superfluous section in environment configuration
        Section: superfluoussection

ERROR: Override section for unknown component found
      Component: nonexisting-component-section

ERROR: Attribute override found both in environment and secrets
      Component: component1
      Attribute: my_attribute

ERROR: Secrets section for unknown component found
      Component: another-nonexisting-component-section
... DEPLOYMENT FAILED (during load) ...
"""
    )  # noqa: E501 line too long


def test_example_errors_gpg_cannot_decrypt(monkeypatch):
    monkeypatch.setitem(os.environ, "GNUPGHOME", "")
    os.chdir("examples/errors")
    out, _ = cmd("./batou deploy errors", acceptable_returncodes=[1])
    assert out == Ellipsis(
        """\
batou/2... (cpython 3...)
No expert/debug flags enabled
Use `batou debug` command to see all available debug settings
... Preparing ...
📦 main: Loading environment `errors`...
🔍 main: Verifying repository ...
🔑 main: Loading secrets ...

ERROR: Error while calling GPG
        command: gpg --decrypt ...environments/errors/secrets.cfg.gpg
      exit code: 2
        message:
gpg: ...
...
ERROR: Failed loading component file
           File: .../examples/errors/components/component5/component.py
      Exception: invalid syntax (component.py, line 1)
Traceback (simplified, most recent call last):
<no-non-remote-internal-traceback-lines-found>

ERROR: Failed loading component file
           File: .../examples/errors/components/component6/component.py
      Exception: No module named 'asdf'
Traceback (simplified, most recent call last):
  File ".../examples/errors/components/component6/component.py", line 1, in <module>
    import asdf  # noqa: F401 import unused
...
ERROR: Missing component
      Component: missingcomponent

ERROR: Superfluous section in environment configuration
        Section: superfluoussection

ERROR: Override section for unknown component found
      Component: nonexisting-component-section
... DEPLOYMENT FAILED (during load) ...
"""
    )  # noqa: E501 line too long


def test_example_errors_late():
    os.chdir("examples/errors2")
    out, _ = cmd("./batou deploy errors", acceptable_returncodes=[1])
    assert out == Ellipsis(
        """\
batou/2... (cpython 3...)
...
📦 main: Loading environment `errors`...
...
🌐 localhost: Connecting via local (1/1)
...
ERROR: Component usage error
...
ERROR: Trying to access address family IPv6...
...
... DEPLOYMENT FAILED (during connect) ...
"""
    )


def test_example_errors_missing_environment():
    os.chdir("examples/errors")
    out, _ = cmd("./batou deploy production", acceptable_returncodes=[1])
    assert out == Ellipsis(
        """\
batou/2... (cpython 3...)
No expert/debug flags enabled
Use `batou debug` command to see all available debug settings
... Preparing ...
📦 main: Loading environment `production`...

ERROR: Missing environment
    Environment: production
... DEPLOYMENT FAILED (during load) ...
"""
    )  # noqa: E501 line too long


def test_example_ignores():
    os.chdir("examples/ignores")
    out, _ = cmd("./batou deploy ignores")
    assert out == Ellipsis(
        """\
batou/2... (cpython 3...)
No expert/debug flags enabled
Use `batou debug` command to see all available debug settings
... Preparing ...
📦 main: Loading environment `ignores`...
🔍 main: Verifying repository ...
🔑 main: Loading secrets ...
... Connecting hosts and configuring model ... ...
🌐 localhost: Connecting via local (1/2)
⏭️ otherhost: Connection ignored (2/2)
... Deploying ...
⚪ localhost: Scheduling component component1 ...
⏭️ localhost: Skipping component fail ... (Component ignored)
⏭️ otherhost: Skipping component fail2 ... (Host ignored)
... Summary ...
Deployment took total=...s, connect=...s, deploy=...s
... DEPLOYMENT FINISHED ...
"""
    )  # noqa: E501 line too long


def test_example_async_sync_deployment():
    os.chdir("examples/sync_async")
    out, _ = cmd("./batou -d deploy default")
    print(out)
    assert "Number of jobs: 1" in out

    out, _ = cmd("./batou -d deploy -j 2 default")
    print(out)
    assert "Number of jobs: 2" in out

    out, _ = cmd("./batou -d deploy async")
    print(out)
    assert "Number of jobs: 2" in out


def test_example_job_option_overrides_environment():
    os.chdir("examples/sync_async")
    out, _ = cmd("./batou -d deploy -j 5 async")
    print(out)
    assert "Number of jobs: 5" in out


def test_consistency_does_not_start_deployment():
    os.chdir("examples/tutorial-helloworld")
    out, _ = cmd("./batou deploy -c tutorial")
    print(out)
    assert "Deploying" not in out
    assert "localhost: Scheduling" not in out
    assert "CONSISTENCY CHECK FINISHED" in out

    # Counter-test that "Deploying" and "localhost: Scheduling" show
    # up if deployments happen
    out, _ = cmd("./batou deploy tutorial")
    print(out)
    assert "Deploying" in out
    assert "localhost: Scheduling" in out
    assert "CONSISTENCY CHECK FINISHED" not in out


def test_diff_is_not_shown_for_keys_in_secrets(tmp_path, monkeypatch, capsys):
    """It does not render diffs for files which contain secrets.

    Secrets might be in the config file in secrets/ or additional encrypted
    files belonging to the environment.
    """
    monkeypatch.chdir("examples/tutorial-secrets")
    if os.path.exists("work"):
        shutil.rmtree("work")
    try:
        out, _ = cmd("./batou deploy tutorial")
    finally:
        if os.path.exists("work"):
            shutil.rmtree("work")
    assert out == Ellipsis(
        """\
batou/2... (cpython 3...)
...
📦 main: Loading environment `tutorial`...
...
🌐 localhost: Connecting via local (1/1)
...
⚪ localhost: Scheduling component hello ...
...
Not showing diff as it contains sensitive data...
...
Deployment took total=...s...
... DEPLOYMENT FINISHED ...
"""
    )


def test_diff_for_keys_in_secrets_overridable(tmp_path, monkeypatch, capsys):
    """It respects the "sensitive_data" flag when showing diffs for
    files which contain secrets

    Secrets might be in the config file in secrets/ or additional encrypted
    files belonging to the environment.
    """

    monkeypatch.chdir("examples/sensitive-values")
    if os.path.exists("work"):
        shutil.rmtree("work")
    try:
        out, _ = cmd("./batou deploy local")
    finally:
        if os.path.exists("work"):
            shutil.rmtree("work")
    assert out == Ellipsis(
        """\
batou/2... (cpython 3...)
...
📦 main: Loading environment `local`...
...
🌐 localhost: Connecting via local (1/1)
...
⚪ localhost: Scheduling component sensitivevalues ...
...
Not showing diff as it contains sensitive data...
...
  hostkey_sensitive_clear_ed25519.pub +ssh-ed25519 ...
...
Deployment took total=...s...
... DEPLOYMENT FINISHED ...
"""
    )


def test_durations_are_shown_for_components():
    os.chdir("examples/durations")
    out, _ = cmd("./batou deploy default")
    assert out == Ellipsis(
        """\
batou/2... (cpython 3...)
No expert/debug flags enabled
Use `batou debug` command to see all available debug settings
... Preparing ...
📦 main: Loading environment `default`...
🔍 main: Verifying repository ...
🔑 main: Loading secrets ...
... Connecting hosts and configuring model ... ...
🌐 localhost: Connecting via local (1/1)
... Deploying ...
⚪ localhost: Scheduling component takeslongtime ...
💤 localhost: Takeslongtime [total=...s, verify=...s, update=∅, sub=∅]
... Summary ...
Deployment took total=...s, connect=...s, deploy=...s
... DEPLOYMENT FINISHED ...
"""
    )


def test_check_consistency_works():
    os.chdir("examples/tutorial-secrets")
    out, _ = cmd("./batou deploy tutorial --consistency-only")
    assert out == Ellipsis(
        """\
batou/2... (cpython 3...)
...
📦 main: Loading environment `tutorial`...
...
🌐 localhost: Connecting via local (1/1)
...
Consistency check took total=...s
... CONSISTENCY CHECK FINISHED ...
"""
    )


def test_predicting_deployment_works():
    os.chdir("examples/tutorial-secrets")
    out, _ = cmd("./batou deploy tutorial --predict-only")
    assert out == Ellipsis(
        """\
batou/2... (cpython 3...)
...
📦 main: Loading environment `tutorial`...
...
🌐 localhost: Connecting via local (1/1)
...
⚪ localhost: Scheduling component hello ...
...
Not showing diff as it contains sensitive data...
...
Deployment took total=...s...
... DEPLOYMENT PREDICTION FINISHED ...
"""
    )


def test_check_consistency_works_with_local():
    os.chdir("examples/tutorial-secrets")
    out, _ = cmd("./batou deploy gocept --consistency-only --local")
    assert out == Ellipsis(
        """\
batou/2... (cpython 3...)
...
📦 main: Loading environment `gocept`...
...
... LOCAL CONSISTENCY CHECK ...
...
Consistency check took total=...s
... CONSISTENCY CHECK (local) FINISHED ...
"""
    )


def test_predicting_deployment_works_with_local():
    os.chdir("examples/tutorial-secrets")
    out, _ = cmd("./batou deploy gocept --predict-only --local")
    assert out == Ellipsis(
        """\
batou/2... (cpython 3...)
...
📦 main: Loading environment `gocept`...
...
🌐 test01: Connecting via local (1/2)
🌐 test02: Connecting via local (2/2)
...
⚪ test01: Scheduling component hello ...
⚪ test02: Scheduling component hello ...
...
Not showing diff as it contains sensitive data...
...
Deployment took total=...s...
... DEPLOYMENT PREDICTION (local) FINISHED ...
"""
    )
