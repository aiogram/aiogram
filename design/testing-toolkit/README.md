# aiogram.test: developer design notes

These notes are for people who change `aiogram.test` ("Testing World"), the integration testing toolkit. The
user-facing documentation is `docs/dispatcher/testing.rst`. This directory is not shipped in the wheel or the
sdist, and is not part of the Sphinx docs.

| File | What it holds |
|---|---|
| [architecture.md](architecture.md) | How the toolkit is put together: the two seams, the call pipeline, a module map and where to add things. |
| [invariants.md](invariants.md) | The rules a change must keep, grouped by area, each with the test file that guards it. |
| [decisions.md](decisions.md) | Why it is built this way: decisions with reasons and the alternatives rejected, plus non-goals, open questions and superseded decisions. |

## Keeping them current

- A change that breaks an invariant updates `invariants.md` in the same PR, or it is a regression.
- A new design choice gets the next `TW-<n>` in `decisions.md`. Code that depends on it cites
  "design decision TW-<n>". IDs are never renumbered.
- The stable user-facing surface is listed in the warning at the top of `docs/dispatcher/testing.rst`.
  Changing a name on that list needs the owner's decision, and the 4.x plans
  (`v4/plans/H-testing-observability/`) must agree.

## Where these came from

The notes were distilled from the OpenSpec specification the toolkit was developed with:

- 34 archived change sets;
- the living specs `bot-testing-environment` and `bot-testing-pytest`.

That specification was removed before the 3.x release. The full text is in the history of `feature/testing`
(PR #1887), in the commit before "Replace the toolkit's OpenSpec files with developer design notes".
