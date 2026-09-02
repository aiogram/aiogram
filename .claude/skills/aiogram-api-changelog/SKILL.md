---
name: aiogram-api-changelog
description: Generate a Bot API changelog fragment (CHANGES/<issue>.misc.rst) for aiogram. Use when the user asks for a changelog entry for a Bot API update, or invokes /aiogram-api-changelog with an issue id and a core.telegram.org changelog URL.
---

# Bot API changelog fragment

Arguments: `<issue_id> <changelog_url>` — e.g. `1792 https://core.telegram.org/bots/api-changelog#april-3-2026`.
If either is missing, ask for it before doing anything else.

## Steps

1. Fetch the changelog URL with WebFetch. Extract **all** changes for the Bot API version anchored by that URL: new methods, new types, new/changed fields, new parameters, renamed fields, and any other notable changes.

2. Discover which aiogram modules were generated for the new symbols:
   - New methods → `aiogram/methods/<snake_case_name>.py` via Glob
   - New types   → `aiogram/types/<snake_case_name>.py` via Glob
   - Confirm every referenced module exists before writing it into the RST.

3. Create `CHANGES/<issue_id>.misc.rst` (overwrite if it exists), following the style used for previous Bot API updates in `CHANGES.rst`:

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
- Use ``:class:`` for types and methods, ``:meth:`` for shortcuts, ``:code:`` for field/parameter names.
- Module paths must be the full dotted path (e.g. `aiogram.types.poll_option.PollOption`), always verified against real files.
- If a symbol has a shortcut method on a type, mention it with ``:meth:``.
- Group related changes under bold section headings (e.g. **Polls**, **Managed Bots**).
- Within each section use italic sub-headings (*New Methods:*, *New Types:*, *New Fields:*, *New Parameters for ...:*) — omit a sub-heading if there is nothing to list under it.
- Describe each item with a brief, user-facing sentence after the dash.
- Do not add a trailing newline after the last bullet.
- Do not include an issue/PR back-reference link (towncrier adds that automatically).

4. Print the path of the created file and confirm it is done.
