#!/bin/sh

set -ex

# Sync all dependencies with uv (reads pyproject.toml + uv.lock)
uv sync --all-groups
