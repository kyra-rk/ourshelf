#!/usr/bin/env bash
# Pushes web/dist/ directly to the gh-pages branch using an isolated temp git
# repo, so the project's .gitignore never interferes.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST="$SCRIPT_DIR/dist"
REMOTE="https://github.com/anum-kyra-officehours/ourshelf.git"
TMPDIR="$(mktemp -d)"

echo "Deploying $DIST → gh-pages..."

cd "$TMPDIR"
git init -b gh-pages
git remote add origin "$REMOTE"
cp -r "$DIST"/. .
git add -f .
git commit -m "deploy web app to gh-pages"
git push -f origin gh-pages

cd /
rm -rf "$TMPDIR"
echo "Done — https://anum-kyra-officehours.github.io/ourshelf/"
