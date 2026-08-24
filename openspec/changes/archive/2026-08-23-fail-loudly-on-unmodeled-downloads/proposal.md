## Why

`FakeTelegramSession.stream_content` yields a single empty chunk, so a handler that
downloads a file gets `b""` and no indication anything is missing:

```python
file = await bot.get_file(file_id=message.document.file_id)
buffer = io.BytesIO()
await bot.download_file(file.file_path, destination=buffer)
assert buffer.getvalue() == b""   # passes, and means nothing
```

A bot that downloads a photo and processes it — resizes it, parses a CSV, checks a
signature — will either take its "empty input" branch in every test, or assert on a result
derived from nothing. Both are green tests for untested code, which is the failure class
this toolkit exists to remove. It is worse than an unmodeled method, because unmodeled
methods at least return a *plausible* object; this returns a value that looks like a real
answer and is not one.

The empty generator was written to keep download paths from raising during the first cut.
That was right then. It should not be the permanent behavior.

## What Changes

- **Downloading a file with no content raises.** `stream_content` raises a clear error
  naming the file and pointing at the two ways to proceed, instead of yielding nothing.
- **Content can be seeded.** A blueprint declares file content by `file_id`
  (`blueprint.add_file("file-id", b"...")`), and the environment serves it to
  `bot.download` / `bot.download_file`. `getFile` — already echoing the requested
  `file_id` — reports a matching size for seeded content.
- **Uploads register their content.** When a handler sends a document whose input is
  `BufferedInputFile`, the bytes it carries are stored against the resulting message's
  `file_id`, so a bot that uploads a file and reads it back in the same test works without
  any declaration.
- The existing escape hatch still applies: `env.on(GetFile).returns(...)` for tests that
  want to control the file object itself.

**BREAKING for tests that download without seeding**: a test that today receives `b""` will
now raise. That is the defect; the error message names the fix.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `bot-testing-environment`: file content becomes declarable world state, and downloading
  content the environment does not have becomes an error rather than an empty result.

## Impact

- **Code**: `aiogram/test/session.py` (`stream_content`), `world.py` (a `files` mapping),
  `blueprint.py` (`add_file`), `modeling.py` (`getFile` size, upload registration).
- **Tests**: a new module under `tests/test_testing/`, holding the package at 100%.
- **Docs**: a "Files and downloads" section in `docs/dispatcher/testing.rst`.
- **Changelog**: `CHANGES/<issue-or-pr>.feature.rst`, calling out the raise explicitly.
- **Risk**: low and bounded. The only judgement call is whether to raise or keep returning
  empty bytes; the design records why raising is the right default for a testing tool.
