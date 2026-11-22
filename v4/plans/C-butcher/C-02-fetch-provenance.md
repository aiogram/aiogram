# C-02 — `fetch`, source cache and manifest provenance

| Field | Value |
|---|---|
| Status | `done` |
| Story | C — Reproducible butcher |
| Target branch | `dev-4.x` |
| Depends on | [C-01](C-01-crate-xtask-ir-snapshot.md) |
| Blocks | [C-24](C-24-scheduled-online-reextract.md), [I-02](../I-distribution/I-02-tier1-wheel-matrix-release.md) |
| Gate-conditional | no |
| Decisions | D118, R24 |
| Sources | [02-butcher.md §2, §5, §6](../../research/02-butcher.md), [19 D118](../../research/19-review-resolutions.md), [codex-review.md R24](../../research/codex-review.md) |
| Size | S (≤1 day) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

R24 found that a committed derived IR can reproduce *emission*, but not *extraction*. D118 resolves this with a manifest
per snapshot (URLs, fetch time, sha256, tool and overlay versions, html-only flag) and immutable raw source bundles
attached to releases. Ordinary CI must never depend on a live page.

## Scope

**In:**
- `cargo xtask butcher fetch [--html URL] [--preview URL] [--openapi URL] [--errors URL] [--cache DIR]`, with defaults:
  - `https://core.telegram.org/bots/api` (HTML);
  - an optional preview page (e.g. `corefork.telegram.org/bots/api`, the legacy `parse-patch`);
  - `<host>/bots/api.json` and `<host>/bots/errors.json`. Today `corefork.` hosts them; `core.` serves the HTML
    fallback (02 §6).
- Cache in `target/butcher-cache/<sha256>` (git-ignored). Each source records URL, HTTP status, fetch time (UTC) and sha256.
- **Detect HTML fallbacks:** an `api.json` URL that returns HTML counts as "unreachable", not as a parse error (02 §6
  says `core.` serves the HTML fallback today).
- `fetch --bundle out.tar.gz` packs the cached raw sources plus `manifest.toml` for release assets.
- `build` reads only from the cache (or `--offline` from a bundle) and fills `manifest.toml` in the snapshot directory
  (schema from C-01).

**Out:** parsing (C-03..C-05), the scheduled job (C-24), uploading the bundle in the release workflow (I-02).

## Checklist

- [x] HTTP client (a blocking `ureq` or `reqwest` with `blocking`, rustls), with timeouts and 3 retries; HTTP only inside `fetch`.
- [x] Content-type and first-byte sniffing, so HTML served at a JSON URL is reported as `unreachable`.
- [x] sha256 for every source; manifest written with stable field order.
- [x] `--bundle` / `--offline BUNDLE`: `build --offline` from a bundle reproduces the same manifest digests.
- [x] Unit tests with a local HTTP fixture server (no network in tests).
- [x] Tests (100% coverage of new code)

## Acceptance criteria

- `fetch` then `build --offline <bundle>` on a second machine produces byte-identical per-adapter IR and manifest digests.
- An `api.json` URL that returns `text/html` is reported as `openapi: unreachable`, and the snapshot is marked `html_only = true` by C-08.
- No test opens a network socket outside localhost (enforced by running the tests with the network disabled in CI).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Commit raw sources in the repo | No license on the schema; commit derived IR only | 02 §6, D118 |
| CI fetches live sources on every PR | Mutable, staging availability; CI is offline | D118 |

## Validation

```bash
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test -p butcher
cargo xtask butcher fetch --cache /tmp/bc && cargo xtask butcher fetch --bundle /tmp/b.tar.gz
```

## Workflow notes

- Runs in parallel with C-03..C-06. C-24 (scheduled job) and I-02 (release assets) consume `fetch --bundle`.

## Notes

- **Cache layout:** `target/butcher-cache/<sha256>` holds a raw source; `fetch.toml` beside them records, per source,
  the URL, status, fetch time and digest (the `sources` table of the snapshot manifest plus the tool version). A bundle
  is a `tar.gz` of `manifest.toml` (the same content) and the digest-named files, with sorted entries and no mtime, so
  the same cache packs to the same bytes.
- **`fetch --bundle`** fetches, then packs; it does not pack without a fetch. Decision: one command, because a bundle
  of an old cache would carry stale fetch times.
- **`build`** resolves its sources from the cache or `--offline BUNDLE` (digests re-verified, no network), then stops at
  the not-implemented stub until C-03..C-08 add parsing. The snapshot `manifest.toml` is assembled there from
  `Fetched::sources`, together with the API version and the overlay and ledger digests.
- **Default hosts:** the page from `core.telegram.org`, `api.json` and `errors.json` from `corefork.telegram.org`;
  `--openapi` / `--errors` override them.
