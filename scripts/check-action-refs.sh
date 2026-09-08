#!/usr/bin/env bash
# Reject action refs that are not version tags or commit SHAs.
# A regex cannot tell a `v7` tag from a `v7` branch, so this does not try to; what it can do is
# reject refs that do not even look like a version tag (`v?1.2.3`) or a 40-hex SHA - `main`,
# `master`, `release/x`, `2.x`, `v4-beta`. That is exactly where zizmor's `ref-pin` policy is
# silent: it checks that a ref is present, not what the ref points at.
set -euo pipefail

cd "$(dirname "$0")/.."

# `pypa/gh-action-pypi-publish@release/v1` is the one documented exception (the ref PyPA
# recommends). Composite actions under `.github/actions/**` are covered too, hence the recursion.
if grep -rnE --include='*.yml' --include='*.yaml' '^[[:space:]]*(-[[:space:]]+)?uses[[:space:]]*:[[:space:]]*[^[:space:]]+@' .github \
     | grep -vE '@(v?[0-9]+(\.[0-9]+)*|[0-9a-f]{40})([[:space:]]|$)' \
     | grep -vE 'pypa/gh-action-pypi-publish@release/v[0-9]+([[:space:]]|$)'; then
  echo "::error::action refs above are not pinned to a version tag or commit SHA"
  exit 1
fi
