#!/bin/sh

set -ex

# Development environment setup with uv
# Usage: ./develop.sh [python version, e.g. 3.12]

python_version="${1:-3.14}"

rm -rf .venv
uv venv --python "$python_version"
uv sync --all-extras --all-groups

set +x

echo
echo "=== BATOU DEV environment ready ==="
echo 'Run commands with uv run prefix or activate with: source .venv/bin/activate'
