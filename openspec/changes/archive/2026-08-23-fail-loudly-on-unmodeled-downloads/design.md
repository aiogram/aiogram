## Context

`BaseSession.stream_content(url, ...)` is the download seam. `Bot.download_file` calls it
with a URL built from `File.file_path` and writes the chunks to a destination. The fake
implements it as `yield b""`, which was the smallest thing that kept download code paths
from raising while the toolkit was being built.

`getFile` already echoes the requested `file_id`, so the identifier a test holds and the
identifier the download refers to are connected. What is missing is anything behind them.

## Goals / Non-Goals

**Goals:**

- No silent empty answer. A download either produces the right bytes or fails saying why.
- Seeding content should be one line, and the common upload-then-download case should need
  none.

**Non-Goals:**

- **Real file storage, paths, or MIME handling.** Content is bytes in a dict keyed by
  `file_id`. No temporary files, no `file_path` semantics beyond what `getFile` already
  synthesizes.
- Media *processing*. Sending a photo still stores a `PhotoSize` with a plausible id and
  derives nothing from the bytes; this change connects downloads to content, it does not
  make the fake understand images.
- Upload size limits, expiry of `file_path`, or the 20MB download ceiling. Policy.

## Decisions

### D1. Raise rather than return empty

The alternative — keep yielding `b""` and document it — was considered and rejected.

A test double may legitimately return a *placeholder* (that is what synthesis does), but a
placeholder must be distinguishable from a real answer. A synthesized `File` object is
obviously synthetic the moment you look at it; `b""` is indistinguishable from "the file
was empty", which is a state real bots handle. The failure mode is a bot whose
empty-input branch is the only branch any test ever exercises.

Raising costs a message and a line in the docs. Returning empty costs somebody a production
bug they had a green test for.

### D2. Content lives in the world, keyed by `file_id`

`World.files: dict[str, bytes]`. Keyed by `file_id` rather than `file_path` because
`file_id` is what a handler actually holds — it comes off the message it just received —
and because `getFile` already echoes it, which makes the two ends meet without a second
lookup table.

`stream_content` receives a *URL*, not an id, so the session recovers the id from the URL
that `getFile` produced. That coupling is the one piece of real machinery here: `getFile`
must mint a `file_path` the session can invert. A path of the form `<file_id>` is enough
and keeps the inversion obvious.

### D3. Uploads register themselves

`BufferedInputFile` carries its bytes. When a send method's media argument is one, the
bytes are stored against the `file_id` the fake mints for the resulting message. The
upload-then-download round trip — the single most common reason a bot touches file
content — then needs no declaration at all.

`FSInputFile` and `URLInputFile` are deliberately *not* read: touching the filesystem or
the network from a fake is exactly what this package promises not to do. They fall through
to the D1 error, and the message says to declare content instead.

### D4. The error names both escapes

The message names the file id and points at `blueprint.add_file(...)` and
`env.on(GetFile).returns(...)`. An error that only says "not modeled" makes the reader go
looking; this one is the documentation for the case where it matters.

## Risks / Trade-offs

- **Existing tests break (D1)** → any test that downloads without seeding now raises. That
  is the defect being fixed, and it is called out in the changelog. Realistically the
  affected population is small: a test asserting on `b""` was asserting nothing.
- **`file_path` inversion couples `getFile` to the session (D2)** → changing one breaks the
  other. Mitigated by a test that goes through the public path end to end
  (`getFile` → `download_file`) rather than testing the inversion in isolation.
- **Someone expects `FSInputFile` to work (D3)** → it looks like it should. Mitigated by
  the error message naming it specifically, and by the docs stating that the fake never
  touches the filesystem.
- **Scope creep toward a file system** → paths, expiry, size limits. Mitigated by the
  non-goals: this is a `dict[str, bytes]`, and it should stay one.

## Migration Plan

One breaking behavior, shipped with its own remedy in the error message. A test that today
downloads and ignores the result should either declare content or override `GetFile`.

## Open Questions

- Should `getFile` fail for an identifier with no content, rather than only the download?
  Leaning no: a bot often calls `getFile` just for the path or size and never downloads,
  and failing there would break more than it protects.
