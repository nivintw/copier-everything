#!/usr/bin/env bash
# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

# One-time helper: create the public GitHub repo for this template and copy the
# branch rulesets from an existing repo (default: nivintw/dotfiles). Uses your local
# `gh` auth — run it from your machine, NOT from CI. Safe to delete after use.
#
# Usage:
#   scripts/bootstrap-github.sh [--repo nivintw/copier-everything] [--from nivintw/dotfiles] [--dry-run]
#
# Requirements: gh (authenticated), jq, git. Run from the repo root with a clean
# `main` already committed.
set -euo pipefail

REPO="nivintw/copier-everything"
FROM="nivintw/dotfiles"
DRY_RUN=false

while [ "$#" -gt 0 ]; do
  case "$1" in
  --repo)
    REPO="$2"
    shift 2
    ;;
  --from)
    FROM="$2"
    shift 2
    ;;
  --dry-run)
    DRY_RUN=true
    shift
    ;;
  *)
    echo "unknown arg: $1" >&2
    exit 2
    ;;
  esac
done

command -v gh >/dev/null || {
  echo "gh not found" >&2
  exit 1
}
command -v jq >/dev/null || {
  echo "jq not found" >&2
  exit 1
}

echo "==> Target repo:  $REPO"
echo "==> Rulesets from: $FROM"
$DRY_RUN && echo "==> DRY RUN (no changes will be made)"

# 1. Create the public repo from this local directory and push main, if it doesn't exist.
if gh repo view "$REPO" >/dev/null 2>&1; then
  echo "==> $REPO already exists — skipping create."
else
  if $DRY_RUN; then
    echo "[dry-run] gh repo create $REPO --public --source=. --remote=origin --push"
  else
    # Ensure a clean main exists locally first.
    git rev-parse --verify main >/dev/null 2>&1 || {
      echo "No local 'main' branch — commit one first." >&2
      exit 1
    }
    gh repo create "$REPO" --public --source=. --remote=origin --push
  fi
fi

# 2. Copy each branch ruleset from $FROM to $REPO.
#    Strip server-managed fields; POST the portable definition.
echo "==> Fetching rulesets from $FROM ..."
ruleset_ids="$(gh api "repos/$FROM/rulesets" --jq '.[].id')"

if [ -z "$ruleset_ids" ]; then
  echo "==> No rulesets found on $FROM."
else
  for id in $ruleset_ids; do
    name="$(gh api "repos/$FROM/rulesets/$id" --jq '.name')"
    echo "==> Ruleset: $name (id $id)"
    body="$(gh api "repos/$FROM/rulesets/$id" |
      jq '{name, target, enforcement, bypass_actors, conditions, rules}')"
    if $DRY_RUN; then
      echo "$body" | jq .
    else
      echo "$body" | gh api --method POST "repos/$REPO/rulesets" --input - &&
        echo "    created on $REPO" ||
        echo "    FAILED (it may already exist, or reference an actor/app not on $REPO)"
    fi
  done
fi

echo "==> Done."
echo "Note: rulesets that require a signed commit / bypass App expect that App to be"
echo "installed on $REPO. Install it and confirm the bypass actor resolved correctly."
