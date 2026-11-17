# G — User-facing additions

Branch: `dev-4.x`. Milestone G of [D121](../../research/19-review-resolutions.md). **Blocks 4.0 GA (PD-01).** That
supersedes the "Additive, 4.x; can ship in 4.0 if ready" wording for `Depends` in
[03 §5](../../research/03-routing.md) and README D32.

## Goal

Ship the features users touch directly, each with its own contract tests:
- dependency injection with teardown (`ParamResolver` + `Depends`);
- i18n absorbed into core (gettext + Fluent, lazy text rendered at encode);
- the formatting API on the Rust entity kernel;
- generated utils signatures;
- bot commands from handlers;
- opt-in retry and rate limiting;
- the built-in `aiogram` CLI;
- the two external deprecation releases (`aiogram_i18n`, `aiogram-cli`).

## Exit gate

- Every G plan's acceptance criteria pass on `dev-4.x`, with its own contract tests (README milestone G).
- The two gate-conditional plans (G-06, G-09) are either done after a B-13 *go*, or re-planned after a no-go.
- Every "Decide X" item is recorded in that plan's Notes and has an owner answer.
- J-06 holds owners and dates for G-20 / G-21.

## Ownership notes

- The **Rust entity kernel** (UTF-16, HTML / MarkdownV2 unparse, quoting) is data plane: **D-17** (PD-15). G-08 only
  builds the Python API on it and runs the parity corpus. HTML / MarkdownV2 *parse* is out of 4.0.
- The **migrate engine** is I-14. G-15 only hosts the `aiogram migrate` command namespace.
- Decision numbering: commands sync is **D60**, lazy `Text` trees **D61**, formatting nodes primary **D62**.
  Generated utils signatures are [06 §4](../../research/06-utils.md) "Defaults" and have no D-number. D59 (album
  middleware) is withdrawn (D116).

## Tasks

| ID | Title | Depends on | Gate-cond. | Size |
|---|---|---|---|---|
| [G-01](G-01-param-resolver-hook.md) | ParamResolver hook | E-02, E-03, E-07 | no | M |
| [G-02](G-02-depends-scope-teardown.md) | `Depends`, per-update scope, teardown (PD-04) | E-11, E-12, E-14, F-02, F-03, G-01 | no | L |
| [G-03](G-03-i18n-core.md) | i18n core: engines, context, managers, lazy values | E-06, E-20 | no | L |
| [G-04](G-04-fluent-engines.md) | Fluent engines | G-03 | no | M |
| [G-05](G-05-utils-i18n-compat.md) | 3.x `aiogram.utils.i18n` compat layer | A-11, G-03 | no | M |
| [G-06](G-06-lazy-text-capture.md) | Lazy text in display fields + capture (PD-07) | B-13, C-06, C-14, C-20, D-10, D-14, E-02, E-14, G-03 | **yes** | L |
| [G-07](G-07-lazy-filter.md) | `LazyFilter` | G-03 | no | S |
| [G-08](G-08-formatting-on-kernel.md) | Formatting nodes on the D-17 kernel | 3x-17, D-17 | no | M |
| [G-09](G-09-lazy-text-trees.md) | Lazy `Text` trees (D61) | D-10, D-17, G-06, G-08 | **yes** | M |
| [G-10](G-10-utils-removals.md) | Utils removals and rewrites | A-11, G-03, I-12 | no | M |
| [G-11](G-11-generated-utils-signatures.md) | Generated utils signatures | C-14, C-17, G-08, G-10 | no | L |
| [G-12](G-12-commands-from-handlers.md) | Bot commands from handlers (D60) | E-04, E-09, G-03 | no | M |
| [G-13](G-13-retry-middleware.md) | `RetryMiddleware` (PD-17, PD-25) | C-06, C-20, D-02, D-03, D-04, D-06, D-10, D-11, D-13, E-12 | no | M |
| [G-14](G-14-rate-limit-middleware.md) | `RateLimitMiddleware` | D-06, D-11, G-13 | no | M |
| [G-15](G-15-cli-core.md) | CLI core, plugins, `info`, `migrate` host | B-01 | no | M |
| [G-16](G-16-cli-run.md) | `run polling` / `run webhook` | E-13, E-15, E-16, E-18, E-23, G-15, H-04 | no | L |
| [G-17](G-17-cli-reload.md) | `--reload` via watchfiles | G-15, G-16 | no | S |
| [G-18](G-18-cli-bot-commands.md) | `bot me / webhook / commands sync` | G-12, G-15 | no | M |
| [G-19](G-19-cli-legacy-plugins.md) | Legacy `aiogram_cli.plugins` + click adapter | A-11, G-15, I-12 | no | S |
| [G-20](G-20-aiogram-i18n-final-release.md) | `aiogram_i18n` mapping + final release | G-03, G-04, G-05, G-06, G-07, G-09 | no | S |
| [G-21](G-21-aiogram-cli-final-release.md) | Final `aiogram-cli` release | G-15, G-19 | no | S |

## Recommended order and parallel lanes

Five lanes are independent of each other inside G. Each starts when its cross-story inputs are done.

1. **CLI**: G-15 → (G-16 → G-17), G-18 (after G-12), G-19 → G-21. G-15 needs only B-01, so it can start earliest.
2. **i18n**: G-03 → G-04, G-05, G-07 in parallel → G-06 (after B-13 *go*, D-10, C-06) → G-09 → G-20.
3. **DI**: G-01 → G-02, once E-02/E-03 and E-11/E-12/E-14/F-02 land.
4. **Formatting & utils**: G-08 (after D-17) and G-10 in parallel → G-11 (after C-17).
5. **Client middlewares**: G-13 → G-14, once D-06/D-10 and the C-06/C-20 `idempotent` metadata land.

G-12 joins after G-03 and E-04/E-09. It feeds G-18.

## Open items carried in plans (owner input needed)

Each is a "Decide X (proposed default)" checklist item in the named plan:
- R17 points (G-02): cache key vs data scopes, double or concurrent handler calls, resolver precedence (G-01),
  cancellation, multiple teardown failures, provider failure during filters, the "flag callables" definition.
- G-06: lazy-value semantics in frozen types (eq / hash / pickle / raw / to_json).
- G-09: `Default("parse_mode")` vs lazy `Text`.
- G-12: command-sync conflicts, order, known languages, `CommandStart` opt-in.
- G-13: the `max_wait` vs `isolation_warn_after` (30 s / 30 s) default clash (the give-up path is settled: E-14 / E-16
  report it through E-12).
- G-14: rate buckets with shared sessions.
- G-15 / G-19: CLI plugin precedence.
- G-16: webhook setup rollback.
- G-03: i18n module path (`aiogram.i18n` proposed).
- G-05: `i18n` data-key collision.
- G-20 / G-21: external package pins and owners.
