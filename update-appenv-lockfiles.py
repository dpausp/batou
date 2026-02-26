#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///
"""Update appenv lockfiles for all examples."""

import subprocess
from pathlib import Path


def check_example(folder: Path) -> list[str]:
    """Check an example folder for correct appenv setup."""
    issues = []

    pyproject = folder / "pyproject.toml"
    appenv = folder / "appenv"
    batou = folder / "batou"
    appenv_py = folder.parent.parent / "appenv.py"

    if not pyproject.exists():
        issues.append("missing pyproject.toml")
        return issues

    if not appenv.exists():
        issues.append("missing appenv")
        return issues

    if not appenv.is_symlink():
        issues.append("appenv is not a symlink")
        return issues

    if appenv.resolve() != appenv_py.resolve():
        issues.append(f"appenv points to {appenv.resolve()}")

    if not batou.exists():
        issues.append("missing batou symlink")
    elif not batou.is_symlink():
        issues.append("batou is not a symlink")
    elif batou.resolve() != appenv.resolve():
        issues.append("batou does not point to appenv")

    return issues


def update_lockfile(folder: Path) -> bool:
    """Run ./appenv update-lockfile in folder."""
    result = subprocess.run(
        ["./appenv", "update-lockfile"],
        cwd=folder,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"  ERROR: {result.stderr}")
        return False

    if output := result.stdout.strip():
        print(f"  {output}")

    # Clean up legacy requirements files
    for name in ("requirements.txt", "requirements.lock"):
        path = folder / name
        if path.exists():
            path.unlink()
            print(f"  Removed {name}")

    return True


def main():
    base = Path(__file__).parent / "examples"

    examples = sorted(
        [f for f in base.iterdir() if f.is_dir() and not f.name.startswith(".")]
    )

    for folder in examples:
        issues = check_example(folder)

        if issues:
            print(f"{folder.name}: {', '.join(issues)}")
            continue

        print(folder.name)
        update_lockfile(folder)


if __name__ == "__main__":
    main()
