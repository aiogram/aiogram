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

3.0.0b1 (2021-12-12)
=====================

Features
--------

- Added new custom operation for MagicFilter named :code:`as_`

  Now you can use it to get magic filter result as handler argument

  .. code-block:: python

      from aiogram import F

      ...

      @router.message(F.text.regexp(r"^(\d+)$").as_("digits"))
      async def any_digits_handler(message: Message, digits: Match[str]):
          await message.answer(html.quote(str(digits)))


      @router.message(F.photo[-1].as_("photo"))
      async def download_photos_handler(message: Message, photo: PhotoSize, bot: Bot):
          content = await bot.download(photo)
  `#759 <https://github.com/aiogram/aiogram/issues/759>`_


Bugfixes
--------

- Fixed: Missing :code:`ChatMemberHandler` import in :code:`aiogram/dispatcher/handler`
  `#751 <https://github.com/aiogram/aiogram/issues/751>`_


Misc
----

- Check :code:`destiny` in case of no :code:`with_destiny` enabled in RedisStorage key builder
  `#776 <https://github.com/aiogram/aiogram/issues/776>`_
- Added full support of `Bot API 5.5 <https://core.telegram.org/bots/api-changelog#december-7-2021>`_
  `#777 <https://github.com/aiogram/aiogram/issues/777>`_
- Stop using feature from #336. From now settings of client-session should be placed as initializer arguments instead of changing instance attributes.
  `#778 <https://github.com/aiogram/aiogram/issues/778>`_
- Make TelegramAPIServer files wrapper in local mode bi-directional (server-client, client-server)
  Now you can convert local path to server path and server path to local path.
  `#779 <https://github.com/aiogram/aiogram/issues/779>`_


3.0.0a18 (2021-11-10)
======================

Features
--------

- Breaking: Changed the signature of the session middlewares
  Breaking: Renamed AiohttpSession.make_request method parameter from call to method to match the naming in the base class
  Added middleware for logging outgoing requests
  `#716 <https://github.com/aiogram/aiogram/issues/716>`_
- Improved description of filters resolving error.
  For example when you try to pass wrong type of argument to the filter but don't know why filter is not resolved now you can get error like this:

  .. code-block:: python3

      aiogram.exceptions.FiltersResolveError: Unknown keyword filters: {'content_types'}
        Possible cases:
        - 1 validation error for ContentTypesFilter
          content_types
            Invalid content types {'42'} is not allowed here (type=value_error)
  `#717 <https://github.com/aiogram/aiogram/issues/717>`_
- **Breaking internal API change**
  Reworked FSM Storage record keys propagation
  `#723 <https://github.com/aiogram/aiogram/issues/723>`_
- Implemented new filter named :code:`MagicData(magic_data)` that helps to filter event by data from middlewares or other filters

  For example your bot is running with argument named :code:`config` that contains the application config then you can filter event by value from this config:

  .. code-block:: python3

      @router.message(magic_data=F.event.from_user.id == F.config.admin_id)
      ...
  `#724 <https://github.com/aiogram/aiogram/issues/724>`_


Bugfixes
--------

- Fixed I18n context inside error handlers
  `#726 <https://github.com/aiogram/aiogram/issues/726>`_
- Fixed bot session closing before emit shutdown
  `#734 <https://github.com/aiogram/aiogram/issues/734>`_
- Fixed: bound filter resolving does not require children routers
  `#736 <https://github.com/aiogram/aiogram/issues/736>`_


Misc
----

- Enabled testing on Python 3.10
  Removed `async_lru` dependency (is incompatible with Python 3.10) and replaced usage with protected property
  `#719 <https://github.com/aiogram/aiogram/issues/719>`_
- Converted README.md to README.rst and use it as base file for docs
  `#725 <https://github.com/aiogram/aiogram/issues/725>`_
- Rework filters resolving:

  - Automatically apply Bound Filters with default values to handlers
  - Fix data transfer from parent to included routers filters
  `#727 <https://github.com/aiogram/aiogram/issues/727>`_
- Added full support of Bot API 5.4
  https://core.telegram.org/bots/api-changelog#november-5-2021
  `#744 <https://github.com/aiogram/aiogram/issues/744>`_


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
