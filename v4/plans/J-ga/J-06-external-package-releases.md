# J-06 — External package releases (aiogram_i18n, aiogram-cli)

| Field | Value |
|---|---|
| Status | `todo` |
| Story | J — GA |
| Target branch | `dev-4.x` (tracking + docs only; the releases happen in their own repositories) |
| Depends on | [G-20](../G-features/G-20-aiogram-i18n-final-release.md), [G-21](../G-features/G-21-aiogram-cli-final-release.md), [I-21](../I-distribution/I-21-fresh-machine-install-rehearsal.md) |
| Blocks | [J-07](J-07-ga-cut-rtd-switch.md) |
| Gate-conditional | no |
| Decisions | D25, D75, D77, R30, 19 §8 |
| Sources | [16-support-policy.md §3](../../research/16-support-policy.md), [17-cli.md D77](../../research/17-cli.md), [19 R30, §8](../../research/19-review-resolutions.md), [06-utils.md §3](../../research/06-utils.md) |
| Size | S (≤1 day) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Two packages are superseded by 4.0 core features:
- `aiogram_i18n`, replaced by core i18n (D25);
- `aiogram-cli`, replaced by the built-in CLI (D75). Today it is 1.1.0, pins `aiogram<4` and ships an `aiogram`
  console script.

Their final releases happen **in their own repositories**. Each needs a named owner and a release date aligned with 4.0.0
GA, tracked as a J item (16 §3, 19 §8).

R30 requires that the final `aiogram-cli` release ships **no `aiogram` console script**, so the two distributions never
own the same script. The docs mention `pip install --force-reinstall aiogram` for broken upgrades.

G-20 (mapping + final release) and G-21 (final aiogram-cli release) prepare the releases. This plan tracks them to GA and
checks the user-visible result.

## Scope

**In:**
- **Tracking table** in this plan's Notes: package, owner, repo PR, planned date (aligned with the J-04 GA date),
  status.
- **Verify** on the release candidate, using the I-21 upgrade scenario:
  - a venv with aiogram 3.x + aiogram-cli 1.1 + aiogram_i18n, then `pip install -U aiogram==<rc> aiogram-cli
    aiogram_i18n`: the final aiogram-cli installs without owning `aiogram`, `aiogram --help` is the built-in CLI, and
    the aiogram_i18n deprecation notice shows;
  - uninstalling `aiogram-cli` afterwards doesn't remove the `aiogram` script (the failure mode `--force-reinstall`
    fixes is documented).
- **Docs.** The migration guide's "External packages" items (J-02) link the final versions. The Install page notes the
  `--force-reinstall` recovery.
- **Release order.** The final `aiogram-cli` and `aiogram_i18n` releases go out **no later than** 4.0.0 GA (proposed:
  the same day, before the aiogram tag). Recorded in the J-05 runbook pre-flight.

**Out:**
- Code in the external repos (G-20, G-21 and their repos).
- The legacy `aiogram_cli.plugins` loader (G-19).

## Checklist

- [ ] Get owner names and dates from the owner, and fill in the tracking table. Flag any missing owner as a GA blocker.
- [ ] Run the upgrade and uninstall scenarios on the rc. Record the pip output in Notes.
- [ ] Docs: `--force-reinstall` note (Install page) and guide links.
- [ ] Add the release order to the J-05 runbook pre-flight.
- [ ] No tests in this repo beyond the I-21 scenario. Changelog fragment `CHANGES/<id>.doc.rst` only if docs change.

## Acceptance criteria

- Both final releases are published (versions recorded) on or before the GA date.
- The upgrade scenario shows exactly one owner of the `aiogram` console script (the `aiogram` distribution).
- An owner is named for each external package.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Shipping an `aiogram` script from the final aiogram-cli | Two distributions owning one script | R30 |
| Keeping aiogram-cli as the CLI | Built-in argparse CLI | D75 |
| Keeping aiogram_i18n as the recommended i18n | Absorbed into core; becomes a migration target | D25 |

## Validation

```bash
uv venv /tmp/up && uv pip install --python /tmp/up/bin/python 'aiogram<4' 'aiogram-cli==1.1.0' aiogram_i18n
uv pip install --python /tmp/up/bin/python -U 'aiogram==<rc>' aiogram-cli aiogram_i18n
/tmp/up/bin/aiogram --help && /tmp/up/bin/python -m pip show -f aiogram-cli | grep -c 'bin/aiogram' || true
```

## Workflow notes

- Inputs: G-20, G-21 (prepared releases), I-21 (upgrade scenario findings), J-04 (GA date).
- Outputs: tracking evidence used by J-07.

## Notes

(empty)
