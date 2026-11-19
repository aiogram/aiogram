# I-11 — uk_UA narrative-only translation pipeline

| Field | Value |
|---|---|
| Status | `todo` |
| Story | I — Distribution & migration beta |
| Target branch | `dev-4.x` |
| Depends on | [I-10](I-10-diataxis-docs-skeleton.md), [I-09](I-09-import-free-docs-build.md) |
| Blocks | — (**not GA-blocking**, proposed default) |
| Gate-conditional | no |
| Decisions | D81 |
| Sources | [18-docs-migration.md D81](../../research/18-docs-migration.md) |
| Size | S (≤1 day) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

The 3.x docs carry 581 uk_UA `.po` files under `docs/locale/uk_UA/`, most of them for the generated reference.
`docs/conf.py` sets `locale_dirs = ["locale/"]` and `gettext_compact = False`, and the Makefile has `docs-gettext` and
`docs-serve-uk_UA` targets.

D81 limits 4.x translation to the narrative docs (Tutorial, Concepts, How-to, Migration). The reference stays English,
because it is Telegram's English text and changes with every Bot API bump. The existing 3.x translations stay with the
3.x docs.

## Scope

**In:**
- gettext extraction limited to the narrative sections. Exclude `reference/**` and autoapi output via
  `gettext_additional_targets` / an exclude pattern in the `.pot` step.
- Start `docs/locale/uk_UA/` empty on `dev-4.x`. The 3.x `.po` files are not carried over, though narrative strings may
  be reused with `msgmerge` against old catalogs where text is unchanged.
- Makefile `docs-gettext` / `docs-serve-uk_UA` ported to the docs group (`uv run --group docs`).
- RTD translation project (or language version) configured for 4.x.
- Mark this plan and its content as **not GA-blocking**.

**Out:**
- Writing the translations. Contributors do that; there is no owner yet.

## Checklist

- [ ] Restrict `.pot` generation to narrative sections. A test asserts no `reference/` `.pot` file is produced.
- [ ] Port the Makefile targets.
- [ ] RTD language project for `dev-4.x`.
- [ ] `msgmerge` helper note in Contributing for reusing 3.x strings.
- [ ] **Record the proposed default: uk_UA is not GA-blocking.** A partial translation ships with a "translation in
      progress" banner. Record it in Notes and flag it to the owner (J-01 checks the flag).
- [ ] No changelog fragment beyond the I-10 docs fragment; no registry entry.

## Acceptance criteria

- `make docs-gettext` produces `.pot` files only for Tutorial / Concepts / How-to / Migration.
- `make docs-serve-uk_UA` (or a one-shot `sphinx-build -D language=uk_UA -W`) builds without warnings with an empty
  catalog.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Translating the generated reference | Telegram's English text, changes per Bot API bump | D81 |
| Carrying 3.x `.po` files forward wholesale | Mostly reference; stays with 3.x docs | D81 |
| Making the translation GA-blocking | No owner/translator; proposed non-blocking | proposed default (this plan) |

## Validation

```bash
uv sync --group docs --no-install-project
make docs-gettext
uv run --no-sync bash -c 'cd docs && sphinx-build -W -D language=uk_UA . _build/html-uk'
```

## Workflow notes

- Input: I-10 tree.
- Independent of everything else; can run any time after I-10.

## Notes

(empty)
