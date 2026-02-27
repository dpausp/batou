import os
import os.path
import shutil

from batou.environment import Environment
from batou.utils import cmd


def test_service_early_resource():
    env = Environment(
        "dev",
        basedir=os.path.dirname(__file__) + "/fixture/service_early_resource",
    )
    env.load()
    env.configure()
    assert env.resources.get("zeo") == ["127.0.0.1:9000"]


def test_example_errors_early(patterns, isolated_example):
    isolated_example("errors")
    out, _ = cmd("./batou deploy errors", acceptable_returncodes=[1])

    patterns.header.optional(
        """\
No expert/debug flags enabled
Use `batou debug` command to see all available debug settings
"""
    )

    # GPG output is variable across versions/systems - make it optional
    # (GPG may fail in some environments like tox with long socket paths)
    patterns.gpg.optional(
        """\
gpg: ...
..."""
    )

    patterns.empty_lines.optional("<empty-line>")

    patterns.errors.merge("header", "gpg", "empty_lines")
    patterns.errors.in_order(
        """\
batou/... (cpython 3...)
... Preparing ...
📦 main: Loading environment `errors`...
🔍 main: Verifying repository ...
🔑 main: Loading secrets ...
<empty-line>
ERROR: Failed loading component file
           File: .../errors/components/component5/component.py
      Exception: invalid syntax (component.py, line 1)
Traceback (simplified, most recent call last):
<no-non-remote-internal-traceback-lines-found>
<empty-line>
ERROR: Failed loading component file
           File: .../errors/components/component6/component.py
      Exception: No module named 'asdf'
Traceback (simplified, most recent call last):
  File ".../errors/components/component6/component.py", line 1, in <module>
    import asdf  # noqa: F401 import unused
<empty-line>
ERROR: Missing component
      Component: missingcomponent
<empty-line>
ERROR: Superfluous section in environment configuration
        Section: superfluoussection
<empty-line>
ERROR: Override section for unknown component found
      Component: nonexisting-component-section
<empty-line>
ERROR: Attribute override found both in environment and secrets
      Component: component1
      Attribute: my_attribute
<empty-line>
ERROR: Secrets section for unknown component found
      Component: another-nonexisting-component-section
... DEPLOYMENT FAILED (during load) ...
"""
    )

    assert patterns.errors == out


def test_example_errors_gpg_cannot_decrypt(monkeypatch, patterns, isolated_example):
    monkeypatch.setitem(os.environ, "GNUPGHOME", "")
    isolated_example("errors")
    out, _ = cmd("./batou deploy errors", acceptable_returncodes=[1])

    patterns.header.optional(
        """\
No expert/debug flags enabled
Use `batou debug` command to see all available debug settings
"""
    )

    # GPG output is variable across versions/systems - make it optional
    patterns.gpg.optional(
        """\
gpg: ...
..."""
    )

    patterns.empty_lines.optional("<empty-line>")

    patterns.errors.merge("header", "gpg", "empty_lines")
    patterns.errors.in_order(
        """\
batou/... (cpython 3...)
... Preparing ...
📦 main: Loading environment `errors`...
🔍 main: Verifying repository ...
🔑 main: Loading secrets ...
<empty-line>
ERROR: Error while calling GPG
        command: gpg --decrypt ...environments/errors/secrets.cfg.gpg
      exit code: 2
        message:
<empty-line>
ERROR: Failed loading component file
           File: .../errors/components/component5/component.py
      Exception: invalid syntax (component.py, line 1)
Traceback (simplified, most recent call last):
<no-non-remote-internal-traceback-lines-found>
<empty-line>
ERROR: Failed loading component file
           File: .../errors/components/component6/component.py
      Exception: No module named 'asdf'
Traceback (simplified, most recent call last):
  File ".../errors/components/component6/component.py", line 1, in <module>
    import asdf  # noqa: F401 import unused
<empty-line>
ERROR: Missing component
      Component: missingcomponent
<empty-line>
ERROR: Superfluous section in environment configuration
        Section: superfluoussection
<empty-line>
ERROR: Override section for unknown component found
      Component: nonexisting-component-section
... DEPLOYMENT FAILED (during load) ...
"""
    )

    assert patterns.errors == out


def test_example_errors_late(patterns, isolated_example):
    isolated_example("errors2")
    out, _ = cmd("./batou deploy errors", acceptable_returncodes=[1])

    patterns.header.optional(
        """\
No expert/debug flags enabled
Use `batou debug` command to see all available debug settings
"""
    )

    patterns.empty_lines.optional("<empty-line>")

    # Catch-all for lines that may appear between expected content
    patterns.any.optional("...")

    patterns.main.merge("header", "empty_lines", "any")
    patterns.main.in_order(
        """\
batou/... (cpython 3...)
... Preparing ...
📦 main: Loading environment `errors`...
🔍 main: Verifying repository ...
🔑 main: Loading secrets ...
... Connecting hosts and configuring model ... ...
🌐 localhost: Connecting via local (1/1)
<empty-line>
ERROR: Component usage error
<empty-line>
ERROR: Trying to access address family IPv6...
<empty-line>
... DEPLOYMENT FAILED (during connect) ...
"""
    )

    assert patterns.main == out


def test_example_errors_missing_environment(patterns, isolated_example):
    isolated_example("errors")
    out, _ = cmd("./batou deploy production", acceptable_returncodes=[1])

    patterns.header.optional(
        """\
No expert/debug flags enabled
Use `batou debug` command to see all available debug settings
"""
    )

    patterns.empty_lines.optional("<empty-line>")

    patterns.main.merge("header", "empty_lines")
    patterns.main.in_order(
        """\
batou/... (cpython 3...)
... Preparing ...
📦 main: Loading environment `production`...
<empty-line>
ERROR: Missing environment
    Environment: production
... DEPLOYMENT FAILED (during load) ...
"""
    )

    assert patterns.main == out


def test_example_ignores(patterns, isolated_example):
    isolated_example("ignores")
    out, _ = cmd("./batou deploy ignores")

    patterns.header.optional(
        """\
No expert/debug flags enabled
Use `batou debug` command to see all available debug settings
"""
    )

    patterns.empty_lines.optional("<empty-line>")

    patterns.main.merge("header", "empty_lines")
    patterns.main.in_order(
        """\
batou/... (cpython 3...)
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
    )

    assert patterns.main == out


def test_example_async_sync_deployment(isolated_example):
    isolated_example("sync_async")
    out, _ = cmd("./batou -d deploy default")
    print(out)
    assert "Number of jobs: 1" in out

    out, _ = cmd("./batou -d deploy -j 2 default")
    print(out)
    assert "Number of jobs: 2" in out

    out, _ = cmd("./batou -d deploy async")
    print(out)
    assert "Number of jobs: 2" in out


def test_example_job_option_overrides_environment(isolated_example):
    isolated_example("sync_async")
    out, _ = cmd("./batou -d deploy -j 5 async")
    print(out)
    assert "Number of jobs: 5" in out


def test_consistency_does_not_start_deployment(isolated_example):
    isolated_example("tutorial-helloworld")
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


def test_diff_is_not_shown_for_keys_in_secrets(isolated_example, capsys, patterns):
    """It does not render diffs for files which contain secrets.

    Secrets might be in the config file in secrets/ or additional encrypted
    files belonging to the environment.
    """
    isolated_example("tutorial-secrets")
    if os.path.exists("work"):
        shutil.rmtree("work")
    try:
        out, _ = cmd("./batou deploy tutorial")
    finally:
        if os.path.exists("work"):
            shutil.rmtree("work")

    patterns.header.optional(
        """\
No expert/debug flags enabled
Use `batou debug` command to see all available debug settings
"""
    )

    patterns.empty_lines.optional("<empty-line>")

    # Catch-all for variable output lines
    patterns.any.optional("...")

    patterns.main.merge("header", "empty_lines", "any")
    patterns.main.in_order(
        """\
batou/... (cpython 3...)
... Preparing ...
📦 main: Loading environment `tutorial`...
🔍 main: Verifying repository ...
🔑 main: Loading secrets ...
🌐 localhost: Connecting via local (1/1)
⚪ localhost: Scheduling component hello ...
Not showing diff as it contains sensitive data...
Deployment took total=...s...
... DEPLOYMENT FINISHED ...
"""
    )

    assert patterns.main == out


def test_diff_for_keys_in_secrets_overridable(isolated_example, capsys, patterns):
    """It respects the "sensitive_data" flag when showing diffs for
    files which contain secrets

    Secrets might be in the config file in secrets/ or additional encrypted
    files belonging to the environment.
    """

    isolated_example("sensitive-values")
    if os.path.exists("work"):
        shutil.rmtree("work")
    try:
        out, _ = cmd("./batou deploy local")
    finally:
        if os.path.exists("work"):
            shutil.rmtree("work")

    patterns.header.optional(
        """\
No expert/debug flags enabled
Use `batou debug` command to see all available debug settings
"""
    )

    patterns.empty_lines.optional("<empty-line>")

    # Catch-all for variable output lines
    patterns.any.optional("...")

    patterns.main.merge("header", "empty_lines", "any")
    patterns.main.in_order(
        """\
batou/... (cpython 3...)
... Preparing ...
📦 main: Loading environment `local`...
🔍 main: Verifying repository ...
🔑 main: Loading secrets ...
🌐 localhost: Connecting via local (1/1)
⚪ localhost: Scheduling component sensitivevalues ...
Not showing diff as it contains sensitive data...
  hostkey_sensitive_clear_ed25519.pub +ssh-ed25519 ...
Deployment took total=...s...
... DEPLOYMENT FINISHED ...
"""
    )

    assert patterns.main == out


def test_durations_are_shown_for_components(patterns, isolated_example):
    isolated_example("durations")
    out, _ = cmd("./batou deploy default")

    patterns.header.optional(
        """\
No expert/debug flags enabled
Use `batou debug` command to see all available debug settings
"""
    )

    patterns.empty_lines.optional("<empty-line>")

    # Catch-all for variable output lines
    patterns.any.optional("...")

    patterns.main.merge("header", "empty_lines", "any")
    patterns.main.in_order(
        """\
batou/... (cpython 3...)
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

    assert patterns.main == out


def test_check_consistency_works(patterns, isolated_example):
    isolated_example("tutorial-secrets")
    out, _ = cmd("./batou deploy tutorial --consistency-only")

    patterns.header.optional(
        """\
No expert/debug flags enabled
Use `batou debug` command to see all available debug settings
"""
    )

    patterns.empty_lines.optional("<empty-line>")

    # Catch-all for variable output lines
    patterns.any.optional("...")

    patterns.main.merge("header", "empty_lines", "any")
    patterns.main.in_order(
        """\
batou/... (cpython 3...)
... Preparing ...
📦 main: Loading environment `tutorial`...
🔍 main: Verifying repository ...
🔑 main: Loading secrets ...
🌐 localhost: Connecting via local (1/1)
Consistency check took total=...s
... CONSISTENCY CHECK FINISHED ...
"""
    )

    assert patterns.main == out


def test_predicting_deployment_works(patterns, isolated_example):
    isolated_example("tutorial-secrets")
    out, _ = cmd("./batou deploy tutorial --predict-only")

    patterns.header.optional(
        """\
No expert/debug flags enabled
Use `batou debug` command to see all available debug settings
"""
    )

    patterns.empty_lines.optional("<empty-line>")

    # Catch-all for variable output lines
    patterns.any.optional("...")

    patterns.main.merge("header", "empty_lines", "any")
    patterns.main.in_order(
        """\
batou/... (cpython 3...)
... Preparing ...
📦 main: Loading environment `tutorial`...
🔍 main: Verifying repository ...
🔑 main: Loading secrets ...
🌐 localhost: Connecting via local (1/1)
⚪ localhost: Scheduling component hello ...
Not showing diff as it contains sensitive data...
Deployment took total=...s...
... DEPLOYMENT PREDICTION FINISHED ...
"""
    )

    assert patterns.main == out


def test_check_consistency_works_with_local(patterns, isolated_example):
    isolated_example("tutorial-secrets")
    out, _ = cmd("./batou deploy gocept --consistency-only --local")

    patterns.header.optional(
        """\
No expert/debug flags enabled
Use `batou debug` command to see all available debug settings
"""
    )

    patterns.empty_lines.optional("<empty-line>")

    # Catch-all for variable output lines
    patterns.any.optional("...")

    patterns.main.merge("header", "empty_lines", "any")
    patterns.main.in_order(
        """\
batou/... (cpython 3...)
... Preparing ...
📦 main: Loading environment `gocept`...
🔍 main: Verifying repository ...
🔑 main: Loading secrets ...
... LOCAL CONSISTENCY CHECK ...
Consistency check took total=...s
... CONSISTENCY CHECK (local) FINISHED ...
"""
    )

    assert patterns.main == out


def test_predicting_deployment_works_with_local(patterns, isolated_example):
    isolated_example("tutorial-secrets")
    out, _ = cmd("./batou deploy gocept --predict-only --local")

    patterns.header.optional(
        """\
No expert/debug flags enabled
Use `batou debug` command to see all available debug settings
"""
    )

    patterns.empty_lines.optional("<empty-line>")

    # Catch-all for variable output lines
    patterns.any.optional("...")

    patterns.main.merge("header", "empty_lines", "any")
    patterns.main.in_order(
        """\
batou/... (cpython 3...)
... Preparing ...
📦 main: Loading environment `gocept`...
🔍 main: Verifying repository ...
🔑 main: Loading secrets ...
🌐 test01: Connecting via local (1/2)
🌐 test02: Connecting via local (2/2)
⚪ test01: Scheduling component hello ...
⚪ test02: Scheduling component hello ...
Not showing diff as it contains sensitive data...
Deployment took total=...s...
... DEPLOYMENT PREDICTION (local) FINISHED ...
"""
    )

    assert patterns.main == out
