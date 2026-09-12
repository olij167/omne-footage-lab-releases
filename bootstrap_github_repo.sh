#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-}"
if [[ -z "$REPO" || "$REPO" != */* ]]; then
  echo "Usage: $0 OWNER/REPOSITORY" >&2
  echo "Example: $0 olij167/omne-footage-lab-releases" >&2
  exit 2
fi
command -v git >/dev/null || { echo "git is required" >&2; exit 2; }
if ! command -v gh >/dev/null 2>&1; then
  cat >&2 <<'EOF'
GitHub CLI (gh) is required before the native build repository can be created.

On Ubuntu/Zorin:
  sudo apt update
  sudo apt install -y gh
  gh auth login

Then re-run this bootstrap command.
EOF
  exit 2
fi

gh auth status
GH_LOGIN="$(gh api user --jq .login)"
VERSION="$(python3 -c 'import ast,pathlib; p=pathlib.Path("app_source/omne_footage_lab.py"); t=ast.parse(p.read_text(encoding="utf-8")); print(next(ast.literal_eval(n.value) for n in t.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=="VERSION" for x in n.targets)))')"

if [[ ! -d .git ]]; then
  git init
  git branch -M main
fi

if [[ -z "$(git config user.name || true)" ]]; then git config user.name "$GH_LOGIN"; fi
if [[ -z "$(git config user.email || true)" ]]; then git config user.email "$GH_LOGIN@users.noreply.github.com"; fi

git add .
if ! git diff --cached --quiet; then
  git commit -m "OmN-e Footage Lab native build pipeline v$VERSION"
fi

if gh repo view "$REPO" >/dev/null 2>&1; then
  REMOTE="https://github.com/$REPO.git"
  if git remote get-url origin >/dev/null 2>&1; then
    git remote set-url origin "$REMOTE"
  else
    git remote add origin "$REMOTE"
  fi
  git push -u origin HEAD:main
else
  if git remote get-url origin >/dev/null 2>&1; then git remote remove origin; fi
  gh repo create "$REPO" --public --source=. --remote=origin --push
fi

echo
echo "Native build repository ready: https://github.com/$REPO"
echo "Start the v$VERSION native release with:"
echo "  gh workflow run native-release.yml -R '$REPO' -f version=$VERSION -f publish_release=true"
echo "Then watch it with:"
echo "  gh run watch -R '$REPO'"
