import os

import pytest


def test_main_with_errors(capsys, patterns):
    os.chdir("examples/errors")

    from batou.deploy import main

    with pytest.raises(SystemExit) as r:
        main(
            environment="errors",
            platform=None,
            timeout=None,
            dirty=False,
            consistency_only=False,
            predict_only=False,
            check_and_predict_local=False,
            jobs=None,
            provision_rebuild=False,
        )

    assert r.value.code == 1

    out, err = capsys.readouterr()
    assert err == ""

    patterns.header.optional(
        """\
No expert/debug flags enabled
Use `batou debug` command to see all available debug settings
"""
    )

    patterns.empty_lines.optional("<empty-line>")

    patterns.any.optional("...")

    patterns.main.merge("header", "empty_lines", "any")
    patterns.main.in_order(
        """\
batou/2... (cpython 3...)
... Preparing ...
📦 main: Loading environment `errors`...
🔍 main: Verifying repository ...
🔑 main: Loading secrets ...
<empty-line>
ERROR: Failed loading component file
           File: .../examples/errors/components/component5/component.py
      Exception: invalid syntax (component.py, line 1)
Traceback (simplified, most recent call last):
<no-non-remote-internal-traceback-lines-found>
<empty-line>
ERROR: Failed loading component file
           File: .../examples/errors/components/component6/component.py
      Exception: No module named 'asdf'
Traceback (simplified, most recent call last):
  File ".../examples/errors/components/component6/component.py", line 1, in <module>
    import asdf  # noqa: F401 import unused
...
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

    assert patterns.main == out


def test_main_fails_if_no_host_in_environment(capsys, patterns):
    os.chdir("examples/errorsnohost")

    from batou.deploy import main

    with pytest.raises(SystemExit) as r:
        main(
            environment="errorsnohost",
            platform=None,
            timeout=None,
            dirty=False,
            consistency_only=False,
            predict_only=False,
            check_and_predict_local=False,
            jobs=None,
            provision_rebuild=False,
        )

    assert r.value.code == 1

    out, err = capsys.readouterr()
    assert err == ""

    patterns.header.optional(
        """\
No expert/debug flags enabled
Use `batou debug` command to see all available debug settings
"""
    )

    patterns.empty_lines.optional("<empty-line>")

    patterns.any.optional("...")

    patterns.main.merge("header", "empty_lines", "any")
    patterns.main.in_order(
        """\
batou/2... (cpython 3...)
... Preparing ...
📦 main: Loading environment `errorsnohost`...
🔍 main: Verifying repository ...
🔑 main: Loading secrets ...
... Connecting hosts and configuring model ... ...
<empty-line>
ERROR: No host found in environment.
... DEPLOYMENT FAILED (during connect) ...
"""
    )

    assert patterns.main == out
