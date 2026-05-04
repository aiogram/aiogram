Generate a Bot API changelog fragment for aiogram.

Arguments: $ARGUMENTS (format: `<issue_id> <changelog_url>`)

## Steps

1. Parse `$ARGUMENTS`: the first token is the issue/PR number (e.g. `1792`), the rest is the changelog URL (e.g. `https://core.telegram.org/bots/api-changelog#april-3-2026`).

2. Fetch the changelog URL using WebFetch. Extract **all** changes for the Bot API version anchored by that URL: new methods, new types, new/changed fields, new parameters, renamed fields, and any other notable changes.

3. Discover which aiogram modules were generated for the new symbols:
   - New methods → search `aiogram/methods/<snake_case_name>.py` via Glob
   - New types   → search `aiogram/types/<snake_case_name>.py` via Glob
   - Confirm every referenced module exists before writing it into the RST.

4. Create `CHANGES/<issue_id>.misc.rst` (overwrite if it exists) with the following RST structure, following the style used for previous Bot API updates in `CHANGES.rst`:

```rst
Updated to `Bot API X.Y <{url}>`_

**{Section heading — e.g. "Feature Area"}**

*New Methods:*

- Added :class:`aiogram.methods.<module>.<ClassName>` method - <short description>

*New Types:*

- Added :class:`aiogram.types.<module>.<ClassName>` type - <short description>

*New Fields:*

- Added :code:`<field>` field to :class:`aiogram.types.<module>.<ClassName>` - <short description>

*New Parameters for* :class:`aiogram.methods.<module>.<ClassName>`:

- Added :code:`<param>` - <short description>
```

Rules for writing the RST:
- Use `:class:`` for types and methods, `:meth:`` for shortcuts, `:code:`` for field/parameter names.
- Module paths must be the full dotted path (e.g. `aiogram.types.poll_option.PollOption`), always verified against real files.
- If a symbol has a shortcut method on a type, mention it with `:meth:`.
- Group related changes under bold section headings (e.g. **Polls**, **Managed Bots**).
- Within each section use italic sub-headings (*New Methods:*, *New Types:*, *New Fields:*, *New Parameters for ...:*) — omit a sub-heading if there is nothing to list under it.
- Describe each item with a brief, user-facing sentence after the dash.
- Do not add a trailing newline after the last bullet.
- Do not include an issue/PR back-reference link (towncrier adds that automatically).

5. Print the path of the created file and confirm it is done.
