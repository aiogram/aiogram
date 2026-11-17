# A-02 — Apply the review resolutions (19) and planning decisions (PD-01..PD-34) to the research pages

| Field | Value |
|---|---|
| Status | `in-progress` |
| Story | A — Contracts & baselines |
| Target branch | `dev-3.x` (where `v4/` is tracked, A-01; merged forward) |
| Depends on | [A-01](A-01-bootstrap-dev-4x.md) |
| Blocks | — (every plan already treats 19 + PDs as normative; this removes the need to) |
| Gate-conditional | no |
| Decisions | D103–D121, PD-01..PD-34 |
| Sources | [19](../../research/19-review-resolutions.md), [plans README §1](../README.md), [codex-review §8](../../research/codex-review.md), all research pages |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. **This is the only plan allowed to
> edit `v4/research/`.** Apply the decisions as recorded; don't make new ones. A contradiction you can't resolve from
> 19 + the PDs goes into *Notes* and to the owner.

## Motivation

Today the normative order is "plans README §1 → 19 → the other pages". A reader of an older page has to remember
which parts are overridden. Milestone A's exit gate includes "19 resolutions applied to all pages" (README D121).
After this plan, each page states its current contract directly, and 19 plus the PD table become history and index.

## Scope

**In:** edit `v4/research/*.md` only, except `codex-review.md`, which stays as the review artifact:
1. **Fold 19 into every page.** Sweep each page for wording that 19 replaced (D103–D121, R03–R30 and 19 §8) and
   rewrite it in place, keeping "(D1xx)" citations. Known remaining spots are listed in the checklist; sweep for
   more.
2. **Fold PD-01..PD-34 into their pages,** using the "Revises" column of the plans README §1. Each folded PD keeps
   its id in the text ("PD-11").
3. **Corrections found during planning,** listed in the checklist.
4. Header status lines: replace "research / planning … No code written yet" with "planned; see `v4/plans/`".

**Out:**
- Changing any decision.
- Editing `codex-review.md`.
- Editing plans, except the plans README §1 "Revises" column, if a page reference turns out wrong.

## Checklist

- [ ] **README.md:**
  - milestone A wording: "behaviour oracle = external pinned 3.x venv; corpus/bench/oracles authored on `dev-3.x`,
    merged forward" (PD-12);
  - architecture box `entities: … render & parse` → `render` (PD-15);
  - D112 row (PD-04);
  - D117 (PD-07);
  - Roadmap: note the pulled-ahead prerequisites (PD-31) and full scope blocking GA (PD-01);
  - D29/D113 unchanged;
  - "Open questions": point to the plans README §1;
  - decision-table rows D59–D62 renumbered to match their pages: D59 album aggregation (withdrawn), D60 commands,
    D61 lazy `Text`, D62 formatting.
- [ ] **4.x-plan-for-core-devs.md** (closed circulation, not in this repository; edit the private copy):
  - fix the broken `rust/README.md` and `rust/19-review-resolutions.md` links (lines 4–5, 66, 104) to `README.md` /
    `19-review-resolutions.md`;
  - "Deferred out of 4.0": remove thread sharding (PD-06).
- [ ] **01-models.md:**
  - §5 title "Spike plan (phase 1)" → "Spike plan (milestone B)";
  - §5.1 "prototype butcher" → hand-written in emitted shape (PD-30);
  - spike not wired into `aiogram.types` (PD-03);
  - §3.1 `timedelta` = absolute `now + delta` (PD-11);
  - §3.3 / §3.4 keyword-only stubs without `**extra` (PD-23).
- [ ] **02-butcher.md:**
  - §3 `import-legacy` is a throwaway Python script behind the xtask shim (PD-10);
  - ErrorReason names pinned in the overlay (PD-24);
  - `idempotent` default and the check (PD-25);
  - remaining helpers port (PD-16);
  - §4 `keep_position` count is 14, not 15, and the `StoryAreaPosition` example is corrected (it is a removed entity
    in the 4.0 ledger reset, 11 §1).
- [ ] **03-routing.md:**
  - §5 Dependencies: teardown inside the isolation scope (PD-04);
  - §5 Dependencies "Additive (4.x; can ship in 4.0 if ready)" → ships in 4.0 and blocks GA (PD-01);
  - D48 warning (PD-05);
  - epoch-bumping containers (PD-18);
  - D111 "matched candidate" definition (PD-19).
- [ ] **04-fsm.md:**
  - §3 one dict + one `threading.Lock`, no shards (PD-21);
  - stdlib `json` default codec (PD-22);
  - Redis/Mongo single-loop (PD-09);
  - re-entrant acquisition raises (PD-26).
- [ ] **05-network.md:**
  - §2.1 timedelta (PD-11; same fix as 13 B17 and 01 §3.1);
  - D46 citation: 13 §3 B9, not 13 §4;
  - §2.3 session `json_*` don't affect the wire and are deprecated (PD-08);
  - §2.5 `API_CALL` per attempt (PD-17) and `idempotent` (PD-25);
  - `DefaultBotProperties` frozen (PD-20);
  - `ClientDecodeError` + `.raw` (PD-29);
  - token-safe errors (PD-14).
- [ ] **06-utils.md:**
  - §1 entity kernel owned by D-17, Python formatting API by G-08 (PD-15);
  - §3 i18n capture points (PD-07).
- [ ] **07-free-threading.md:**
  - line 18 "Design detail to be done in phase 4" → "milestone E (E-19)";
  - single-bot sharding ships in 4.0 (PD-06);
  - Redis/Mongo single-loop (PD-09);
  - Tier-1 meaning (PD-27).
- [ ] **08-build-release.md:**
  - §4 Tier 1 = our wheels + our suite (PD-27);
  - §5 differential harnesses run against an external pinned 3.x venv (PD-12);
  - §5 "Python fallback encoder" contradicts D1 (mandatory core, no pure-Python fallback): remove it;
  - benchmarks: name the A-05 harness and drop "pytest-codspeed or asv" if A-05 chose otherwise.
- [ ] **09-3x-quick-wins.md:**
  - #18 dropped (PD-28);
  - #8 measure-or-drop (PD-28);
  - #21 uses the per-update-on-failure shape (PD-28);
  - behaviour-changing items ship in a minor (PD-28);
  - add the R27 notes that D120 didn't carry: #4 (pruning must count holders and waiters), #12 (a bare lock bypasses
    bookkeeping; folded into 3x-06), #5 (first-use concurrency), #14 (defaults, session ownership, use across loops);
  - link each row to its 3x plan.
- [ ] **10-forward-compatibility.md:**
  - Layer 2: `TelegramDecodeError` → `ClientDecodeError` with `.raw` (PD-29);
  - §5: link 3x-01 / 3x-02 / A-03 and the "emit to errors" decision A-03 recorded.
- [ ] **11-removals.md:** §4 `force_reply` on `as_markup` is **stale**. Bot API 10.4 added `force_reply` to
      `InlineKeyboardMarkup` and `ReplyKeyboardMarkup` (aiogram 3.32, #1954), so it is a real field, not a leak, and
      4.0 keeps it (G-10 / I-16 don't remove it). Remove the row and the matching test note in §7, or reword it per
      the owner. Flag the change to the owner.
- [ ] **13-aiogram-rust-review.md:**
  - B8 "README roadmap phase 2/4", B9 "phase 3", B24 "README phase 1" → milestone letters (B, D, E);
  - B17 timedelta (PD-11).
- [ ] **14-testing.md:** §3 "port during roadmap phase 4" → "milestone H".
- [ ] **15-observability.md:**
  - §5: the 3.x fix shape is PD-14 (same type, redacted, `from None`, original on `.original`);
  - H owns only the log filters; D-03 owns the 4.x wrapping;
  - `API_CALL` spans per attempt (PD-17).
- [ ] **16-support-policy.md:**
  - §2 baseline list: add D96 `TelegramMethod` subclasses, `UnsupportedKeywordArgument`, `Recommendation`, the 122
    API-ledger fields and 3 entities, and `create_channel_bot_link(parameter=)`;
  - state that D100 positional calls get **no runtime warning** (checker only);
  - registry = `registry.toml` (PD-13);
  - §1 "the registry fails CI once an entry's removal version is reached" → the D71 / R28 rule (due after 12 months
    **and** 2 minors, then an explicit `removal_decision` is required; I-12);
  - §2: remove `force_reply` from the removal list per the 11 item (real Bot API 10.4 field, #1954).
- [ ] **18-docs-migration.md:** §2 `aiogram/_migration/registry.py` → `registry.toml`, read by path, ids `AG4xxx`
      append-only, three kinds (PD-13).
- [ ] **12-runtime.md:** §6 webhook prerequisites: name the 3.x webhook background-task drain fix. Drop any "missing
      `dispatcher`/`bots` webhook kwargs" prerequisite: the `dispatcher` kwarg is already fixed by #1856 and `bots` is
      polling-only by design.
- [ ] **PD-32..PD-34:** PD-32 into 11 §4 / 16 §2 (the `force_reply` items above); PD-33 (registry authority and id
      blocks) into 18 §2 and 16 §1 next to PD-12 / PD-13; PD-34 (embargo) has no research target — note it in the
      README roadmap's milestone A wording only.
- [ ] **19-review-resolutions.md:** add "revised by PD-xx" pointers at D112 (PD-04), D117 (PD-07) and R22 (PD-14).
      Don't rewrite the resolutions.
- [ ] Sweep: `grep -rniE "phase [0-9]|roadmap phase|registry\.py|TelegramDecodeError|timedelta as seconds|last 3\.x
      minor" v4/research --exclude=codex-review.md` returns only intended hits.
- [ ] Link check: every relative Markdown link in `v4/research` and `v4/plans` resolves (script below).
- [ ] Changelog: none (internal docs). Use the `skip news` label.

## Acceptance criteria

- The sweep grep above returns no unintended matches.
- The link check reports 0 broken links.
- Each PD id from PD-01 to PD-34 appears at least once in the page(s) its "Revises" column names (PD-34, with no
  "Revises" target, in the README milestone A wording); a loop over the 34 ids checks this.
- `git diff --stat` touches only `v4/research/` (and the plans README §1 if a reference was corrected).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Leave the pages and rely on "19 wins" | Every reader has to re-derive the contract; milestone A requires the pages updated | D121 |
| Rewrite `codex-review.md` | It is kept as the review artifact | README docs table |

## Validation

```bash
grep -rniE "phase [0-9]|roadmap phase|registry\.py|TelegramDecodeError|last 3\.x minor" v4/research --exclude=codex-review.md
python3 - <<'EOF'
import pathlib, re, sys
bad = []
for f in pathlib.Path("v4").rglob("*.md"):
    for link in re.findall(r"\]\(([^)#\s]+)", f.read_text()):
        if "://" in link:
            continue
        if not (f.parent / link).exists():
            bad.append(f"{f}: {link}")
print("\n".join(bad))
sys.exit(1 if bad else 0)
EOF
```

## Workflow notes

- Runs after A-01. It can run in parallel with every other plan, because nothing waits on it: plans already treat
  19 and the PDs as normative.
- If a PD has no clear target page, record it in Notes and don't invent one.

## Notes
