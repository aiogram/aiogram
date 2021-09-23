=========
Changelog
=========

..
    You should *NOT* be adding new change log entries to this file, this
    file is managed by towncrier. You *may* edit previous change logs to
    fix problems like typo corrections or such.
    To add a new change log entry, please see
    https://pip.pypa.io/en/latest/development/#adding-a-news-entry
    we named the news folder "CHANGES".

    WARNING: Don't drop the next directive!

.. towncrier release notes start

3.0.0a17 (2021-09-24)
======================

Misc
----

- Added :code:`html_text` and :code:`md_text` to Message object
  `#708 <https://github.com/aiogram/aiogram/issues/708>`_
- Refactored I18n, added context managers for I18n engine and current locale
  `#709 <https://github.com/aiogram/aiogram/issues/709>`_


3.0.0a16 (2021-09-22)
======================

Features
--------

- Added support of local Bot API server files downloading

  When Local API is enabled files can be downloaded via `bot.download`/`bot.download_file` methods.
  `#698 <https://github.com/aiogram/aiogram/issues/698>`_
- Implemented I18n & L10n support
  `#701 <https://github.com/aiogram/aiogram/issues/701>`_


Misc
----

- Covered by tests and docs KeyboardBuilder util
  `#699 <https://github.com/aiogram/aiogram/issues/699>`_
- **Breaking!!!**. Refactored and renamed exceptions.

  - Exceptions module was moved from :code:`aiogram.utils.exceptions` to :code:`aiogram.exceptions`
  - Added prefix `Telegram` for all error classes
  `#700 <https://github.com/aiogram/aiogram/issues/700>`_
- Replaced all :code:`pragma: no cover` marks via global :code:`.coveragerc` config
  `#702 <https://github.com/aiogram/aiogram/issues/702>`_
- Updated dependencies.

  **Breaking for framework developers**
  Now all optional dependencies should be installed as extra: `poetry install -E fast -E redis -E proxy -E i18n -E docs`
  `#703 <https://github.com/aiogram/aiogram/issues/703>`_


3.0.0a15 (2021-09-10)
======================

Features
--------

- Ability to iterate over all states in StatesGroup.
  Aiogram already had in check for states group so this is relative feature.
  `#666 <https://github.com/aiogram/aiogram/issues/666>`_


Bugfixes
--------

- Fixed incorrect type checking in the :class:`aiogram.utils.keyboard.KeyboardBuilder`
  `#674 <https://github.com/aiogram/aiogram/issues/674>`_


Misc
----

- Disable ContentType filter by default
  `#668 <https://github.com/aiogram/aiogram/issues/668>`_
- Moved update type detection from Dispatcher to Update object
  `#669 <https://github.com/aiogram/aiogram/issues/669>`_
- Updated **pre-commit** config
  `#681 <https://github.com/aiogram/aiogram/issues/681>`_
- Reworked **handlers_in_use** util. Function moved to Router as method **.resolve_used_update_types()**
  `#682 <https://github.com/aiogram/aiogram/issues/682>`_


3.0.0a14 (2021-08-17)
======================

Features
--------

- add aliases for edit/delete reply markup to Message
  `#662 <https://github.com/aiogram/aiogram/issues/662>`_
- Reworked outer middleware chain. Prevent to call many times the outer middleware for each nested router
  `#664 <https://github.com/aiogram/aiogram/issues/664>`_


Bugfixes
--------

- Prepare parse mode for InputMessageContent in AnswerInlineQuery method
  `#660 <https://github.com/aiogram/aiogram/issues/660>`_


Improved Documentation
----------------------

- Added integration with :code:`towncrier`
  `#602 <https://github.com/aiogram/aiogram/issues/602>`_


Misc
----

- Added `.editorconfig`
  `#650 <https://github.com/aiogram/aiogram/issues/650>`_
- Redis storage speedup globals
  `#651 <https://github.com/aiogram/aiogram/issues/651>`_
- add allow_sending_without_reply param to Message reply aliases
  `#663 <https://github.com/aiogram/aiogram/issues/663>`_
