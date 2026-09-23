#!/usr/bin/env bash
# Commits the given paths as the bot and pushes to the branch the workflow runs on.
#
# Why this exists: the bot jobs write generated files (pages, facts, the spend ledger). When two jobs push in the
# same hour, `git pull --rebase` used to stop on a conflict and the whole run's output was lost — including the
# ledger of paid model calls (23 September 2026: six daily runs in a row). Generated files are never hand-edited,
# so a conflict is resolved by keeping this run's version and the push is retried.
#
# Usage: scripts/commit_push.sh "<commit message>" <path>...
set -euo pipefail
msg="$1"; shift
git config user.name "trade-rules-bot"
git config user.email "bot@users.noreply.github.com"
for p in "$@"; do
  if [ -e "$p" ]; then git add -A -- "$p"; fi
done
if git diff --cached --quiet; then
  echo "no changes"
  exit 0
fi
git commit -q -m "$msg"
branch="${GITHUB_REF_NAME:-$(git rev-parse --abbrev-ref HEAD)}"
for attempt in 1 2 3 4; do
  git fetch -q origin "$branch"
  if ! git rebase -q "origin/$branch"; then
    conflicted="$(git diff --name-only --diff-filter=U)"
    echo "rebase conflict — keeping this run's version of: $conflicted"
    # during a rebase "theirs" is the commit being replayed, i.e. this run's files
    echo "$conflicted" | xargs -r git checkout --theirs --
    echo "$conflicted" | xargs -r git add --
    GIT_EDITOR=true git rebase --continue
  fi
  if git push -q origin "HEAD:$branch"; then
    echo "pushed: $msg"
    exit 0
  fi
  echo "push rejected (attempt $attempt), retrying"
  sleep $((attempt * 5))
done
echo "push failed after 4 attempts" >&2
exit 1
