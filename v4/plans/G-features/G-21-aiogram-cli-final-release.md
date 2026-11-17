# G-21 — Final `aiogram-cli` release

| Field | Value |
|---|---|
| Status | `todo` |
| Story | G — User-facing additions |
| Target branch | `dev-4.x` (docs + registry) + the `aiogram-cli` repository (final release) |
| Depends on | [G-15](G-15-cli-core.md), [G-19](G-19-cli-legacy-plugins.md) |
| Blocks | [J-06](../J-ga/J-06-external-package-releases.md), [I-23](../I-distribution/I-23-beta-pre-release.md) |
| Gate-conditional | no |
| Decisions | D77, D68, R30, PD-13 |
| Sources | [17-cli.md D77](../../research/17-cli.md), [19 R30, §8](../../research/19-review-resolutions.md), [16-support-policy.md §3](../../research/16-support-policy.md), [codex-review.md R30](../../research/codex-review.md) |
| Size | S (≤1 day) in this repo; external release effort tracked by J-06 |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

aiogram 4.0 ships its own `aiogram` console script (G-15). If the old `aiogram-cli` distribution also owns
`aiogram`, the two overwrite each other on install and uninstall. Per R30, the final `aiogram-cli` release ships
**no `aiogram` console script**, and the docs give `pip install --force-reinstall aiogram` for broken upgrades.

## Scope

**In (this repository):**
- An upgrade note in the CLI docs and migration guide:
  - uninstall `aiogram-cli`;
  - `aiogram[cli]` is gone (D68);
  - the `--force-reinstall aiogram` recipe;
  - legacy plugins keep working for one window (G-19).
- A migration-registry entry (PD-13) for the `aiogram-cli` package deprecation, unless G-15 already added it with
  the `cli` extra removal (check and link).

**In (external repository; executed by its owner, tracked by J-06):**
- A final release that:
  - removes the `aiogram` console-script entry point;
  - prints an uninstall notice when imported or run via `python -m aiogram_cli`;
  - keeps exporting the `aiogram_cli.plugins` entry-point group machinery, so G-19's adapter still finds plugins.

**Out:**
- Maintaining `aiogram-cli` after the final release.

## Checklist

- [ ] Docs upgrade note (CLI page + migration guide section).
- [ ] Registry entry (or link to G-15's).
- [ ] **Decide the final release's aiogram requirement** (the 1.x line pins `aiogram<4`). Proposed default: drop the
      upper pin and require nothing from aiogram, so `pip install -U aiogram aiogram-cli` resolves to aiogram 4 plus
      a script-less `aiogram-cli` instead of downgrading aiogram. Record in Notes and flag to owner.
- [ ] **Decide the owner and the release date** (aligned with 4.0.0 GA) — record in Notes and hand to J-06.
- [ ] Rehearsal: in a fresh venv, install `aiogram<4` + `aiogram-cli` 1.1.0, then upgrade to aiogram 4 + the final
      `aiogram-cli` (from a test index or wheel). `aiogram --help` must resolve to the core CLI. Record the result in
      Notes and feed it to I-22.
- [ ] Changelog fragment (`doc`).

## Acceptance criteria

- The rehearsal above ends with `aiogram --help` showing the core CLI's usage. `pip uninstall aiogram-cli` afterwards
  leaves `aiogram` working.
- J-06 has the owner, date and release checklist.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Final `aiogram-cli` keeps an `aiogram` script | Two distributions owning one script break on upgrade/uninstall | R30 |
| Keeping the `cli` extra pointing at `aiogram-cli` | CLI is built in | D68 |

## Validation

```bash
uv run --group docs --no-install-project bash -c 'cd docs && make html'   # R29; docs is a dependency group in 4.x (D68)
make lint
uv run pytest tests
```

## Workflow notes

- Inputs: G-15 (console script), G-19 (legacy plugin adapter).
- Output: J-06 (external release), I-22 (migration rehearsal includes the CLI upgrade).

## Notes
