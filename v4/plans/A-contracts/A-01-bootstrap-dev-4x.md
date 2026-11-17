# A-01 — Bootstrap `dev-4.x`, commit the planning tree, define the sync policy

| Field | Value |
|---|---|
| Status | `in-progress` |
| Story | A — Contracts & baselines |
| Target branch | `dev-3.x` (commit `v4/`) and new `dev-4.x` |
| Depends on | — |
| Blocks | [A-02](A-02-apply-resolutions.md), [B-01](../B-spike/B-01-crate-maturin-skeleton.md), [C-01](../C-butcher/C-01-crate-xtask-ir-snapshot.md) (every `dev-4.x` plan), [A-11](A-11-migration-registry.md), [D-01](../D-client/D-01-default-bot-properties-and-bot-cleanup.md), [D-02](../D-client/D-02-exceptions-error-reason-restarting-removal.md), [D-03](../D-client/D-03-token-safe-network-errors.md), [D-04](../D-client/D-04-drop-aiofiles-input-file-replayable.md), [D-06](../D-client/D-06-request-middleware-manager.md), [E-01](../E-runtime/E-01-dispatcher-filter-removals.md), [E-02](../E-runtime/E-02-dispatch-table-executor.md), [F-01](../F-fsm/F-01-thread-safe-memory-storage.md), [F-02](../F-fsm/F-02-isolation-lock-table-default-on.md), [F-04](../F-fsm/F-04-fsm-hot-paths-statefilter.md), [F-08](../F-fsm/F-08-shared-converter-core.md), [H-01](../H-testing-observability/H-01-logger-hierarchy.md), [H-05](../H-testing-observability/H-05-trace-hook-core.md), [H-10](../H-testing-observability/H-10-testing-world-import.md), [H-19](../H-testing-observability/H-19-mockedbot-port.md) |
| Gate-conditional | no |
| Decisions | D121, PD-03, PD-12, PD-34 |
| Sources | [README roadmap](../../research/README.md), [plans README](../README.md), [08 §2, §6](../../research/08-build-release.md) |
| Size | S (≤1 day) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Every 4.0 plan targets `dev-4.x`, which doesn't exist yet. The research (`v4/research/`) and these plans
(`v4/plans/`) are **untracked** in the `dev-3.x` worktree (`git status` shows `?? v4/`). Plans flip their own
`Status` in the PR that implements them (plans README, "Running plans"). 3x and A plans land on `dev-3.x`, so the
tree has to be tracked there too. Corpus, bench and oracles are authored on `dev-3.x` and merged forward (PD-12).

## Scope

**In:**
- **Embargo check before anything is pushed.** Nothing that names or describes an unfixed security issue may be
  pushed (PD-34). `4.x-plan-for-core-devs.md` is marked "closed circulation". The repository is public.
- Commit `v4/research/` and `v4/plans/` on `dev-3.x`, in one commit with no other changes.
- Create `dev-4.x` from `dev-3.x` at that commit and push it. Add branch protection and CI on par with `dev-3.x`
  (existing workflows, triggered for `dev-4.x` too).
- **Sync policy**, written into `v4/plans/README.md` §"Running plans" (this plan may edit that one file):
  1. Until C-18 / C-13 replace the generated code on `dev-4.x`, merge `dev-3.x` into `dev-4.x` regularly (at least
     after each 3.x release, and after each A plan lands).
  2. After that, cherry-pick hand-written 3.x fixes only. Generated-code conflicts are resolved by regenerating on
     `dev-4.x`.
  3. `aiogram/_migration/registry.toml` follows A-11's authority rule, not this merge direction.
  4. `v4/plans/` status flips merge forward like any other file.
- Exclude `v4/` from the built sdist and wheel.

**Out:**
- The `dev-4.x` build skeleton (maturin, crates): B-01.
- Research page edits: A-02.

## Checklist

- [ ] Embargo check: every issue the tree names or describes is either fixed and released or already public; the
  rest is redacted, and plans whose substance is an unfixed fix are held back (PD-34). Keep the core-dev brief
  (`4.x-plan-for-core-devs.md`) in closed circulation, out of the public tree. Record the result in Notes.
- [ ] Check `v4/` is excluded from packaging (`[tool.hatch.build]` in `pyproject.toml`). Add an `exclude` if hatch
      would include it. Verify with `uv build` and list the sdist contents.
- [ ] Commit `v4/` on `dev-3.x`, without the stray files from the worktree (`dialogue.md`, local archives,
      `html-css-widget.html`, which aren't part of this plan).
- [ ] Create and push `dev-4.x`. Enable the existing CI workflows for it: check the `branches:` filters in
      `.github/workflows/*.yml`; `make lint-workflows` if they change.
- [ ] Write the sync policy into `v4/plans/README.md`.
- [ ] Changelog: none, because there is no user-visible change. CI on `dev-3.x` requires a fragment or the `skip
      news` label, so use the label.

## Acceptance criteria

- `git ls-tree -r --name-only origin/dev-3.x v4 | wc -l` equals the number of files under `v4/`.
- `origin/dev-4.x` exists, and CI runs and passes on it with the same jobs as `dev-3.x`.
- The built sdist and wheel contain no `v4/` path.
- The PD-34 embargo check result is recorded in Notes; held-back plans are not pushed before their fixes ship.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Keep `v4/` only on `dev-4.x` | 3x / A plans couldn't flip their status in their own PRs | plans README |
| An in-tree 3.x reference path inside 4.0 instead of an external venv | The behaviour oracle is an external pinned 3.x venv | PD-12 |

## Validation

```bash
git ls-tree -r --name-only origin/dev-3.x v4 | head
git ls-remote --heads origin dev-4.x
uv build && tar tzf dist/aiogram-*.tar.gz | grep -c '^aiogram-[^/]*/v4/' || true   # must print 0
make lint-workflows   # only if workflow files changed
```

## Workflow notes

- **Outputs:** the `dev-4.x` branch and the sync policy. Every 4.0 story starts from them.
- A-02 runs right after this plan, so the committed pages become normative.

## Notes

- Owner, 2026-11-18: **redact and commit now** (PD-34 revised): descriptions of unfixed security issues are
  removed, plans whose substance is an unfixed fix (3x-02, 3x-15, 3x-19) are held back until released, and
  `4.x-plan-for-core-devs.md` stays out (closed circulation). The owner reviews the redacted tree before the push.
- The unredacted tree stays canonical outside this repository; held-back files are committed after their fix ships.

- Embargo check, 2026-11-18: the committed tree names no unfixed security issue; 3x-02, 3x-15 and 3x-19 are held
  back; the text-decoration escaping fix (#1979) shipped in 3.32.0; the polling stall is public (#1840 / #1890).
