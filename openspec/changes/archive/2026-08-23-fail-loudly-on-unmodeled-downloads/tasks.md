## 1. Content in the world

- [x] 1.1 Add `World.files: dict[str, bytes]` (design D2)
- [x] 1.2 Add `Blueprint.add_file(file_id, content)` and deep-copy it into the environment
- [x] 1.3 Make `getFile` report a size matching held content, keeping the existing `file_id` echo
- [x] 1.4 Mint a `file_path` the session can invert back to the `file_id`
- [x] 1.5 Tests: declared content downloads; size matches; environments stay isolated

## 2. Failing loudly

- [x] 2.1 Replace the empty generator in `stream_content` with a lookup by inverted `file_id` (design D1)
- [x] 2.2 Raise naming the file id and both escapes — `blueprint.add_file(...)` and `env.on(GetFile).returns(...)` (design D4)
- [x] 2.3 Regression test: downloading undeclared content raises rather than producing `b""` — the case that currently passes meaninglessly
- [x] 2.4 Test: the error surfaces through `bot.download` and `bot.download_file`, not just `stream_content`

## 3. Uploads

- [x] 3.1 Store the bytes of a `BufferedInputFile` against the resulting message's file id (design D3)
- [x] 3.2 Leave `FSInputFile` and `URLInputFile` unread, falling through to the D1 error with a message naming them
- [x] 3.3 Test: upload then download round-trips within one test with no declaration
- [x] 3.4 Test: a filesystem-backed input raises rather than reading the disk

## 4. Documentation

- [x] 4.1 Add a "Files and downloads" section to `docs/dispatcher/testing.rst`
- [x] 4.2 Show the upload round trip, the declaration, and the override
- [x] 4.3 State that the fake never reads the filesystem or the network, and why the download raises instead of returning empty
- [x] 4.4 Build docs and fix any new warnings

## 5. Release readiness

- [x] 5.1 No new fragment: the toolkit is unreleased, so this folded into its existing `CHANGES/1874.feature.rst` entry
- [x] 5.2 Full check loop green: `rtk ruff format`, `rtk ruff check --show-fixes --preview aiogram examples`, `rtk mypy aiogram`, `rtk test uv run pytest tests -q --cov=aiogram --cov-report=term-missing` at 100%
