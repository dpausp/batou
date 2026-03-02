#!/bin/bash
set -euo pipefail

current_branch=$(git rev-parse --abbrev-ref HEAD)

if [ "$current_branch" != "main" ]; then
    echo "ERROR: can only release from main. We are on $current_branch" >&2
    exit 1
fi

changes=$(git status --porcelain)
if [ -n "$changes" ]; then
    echo "ERROR: there are uncommitted changes." >&2
    git status
    exit 1
fi

cd "$(dirname "$0")"

# Collect changelog entries with scriv
uvx scriv collect

# Remove "Nothing changed yet" section (macOS/BSD sed compatible)
sed -i '' '/- Nothing changed yet./ { N; d; }' CHANGES.md

git add -A .
git status
PAGER= git diff --cached

echo "Press enter to commit changelog and start release, Ctrl-C to abort."
read -r

git commit -m "Prepare changelog for release"

# Run fullrelease via uv
uvx --from zest.releaser fullrelease
