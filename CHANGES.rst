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

.. towncrier-draft-entries:: [UPCOMING UPDATE]

.. towncrier release notes start

3.25.0 (2026-02-10)
====================

Features
--------

- Add full_name property to Contact and corresponding tests
  `#1758 <https://github.com/aiogram/aiogram/issues/1758>`_
- Updated to `Bot API 9.4 (February 9, 2026) <https://core.telegram.org/bots/api-changelog#february-9-2026>`_

  **New Features:**

  - Bots with Premium subscriptions can now use custom emoji directly in messages to private, group, and supergroup chats
  - Bots can create topics in private chats via the :class:`aiogram.methods.create_forum_topic.CreateForumTopic` method
  - Bots can prevent users from creating/deleting topics in private chats through BotFather settings

  **New Fields:**

  - Added :code:`allows_users_to_create_topics` field to :class:`aiogram.types.user.User` class - indicates whether the user allows others to create topics in chats with them
  - Added :code:`icon_custom_emoji_id` field to :class:`aiogram.types.keyboard_button.KeyboardButton` and :class:`aiogram.types.inline_keyboard_button.InlineKeyboardButton` classes - allows displaying custom emoji icons on buttons
  - Added :code:`style` field to :class:`aiogram.types.keyboard_button.KeyboardButton` and :class:`aiogram.types.inline_keyboard_button.InlineKeyboardButton` classes - changes button color/style
  - Added :code:`chat_owner_left` field to :class:`aiogram.types.message.Message` class - service message indicating chat owner has left (type: :class:`aiogram.types.chat_owner_left.ChatOwnerLeft`)
  - Added :code:`chat_owner_changed` field to :class:`aiogram.types.message.Message` class - service message indicating chat ownership has transferred (type: :class:`aiogram.types.chat_owner_changed.ChatOwnerChanged`)
  - Added :code:`qualities` field to :class:`aiogram.types.video.Video` class - list of available video quality options (type: :code:`list[`:class:`aiogram.types.video_quality.VideoQuality`:code:`]`)
  - Added :code:`first_profile_audio` field to :class:`aiogram.types.chat_full_info.ChatFullInfo` class - user's first profile audio
  - Added :code:`rarity` field to :class:`aiogram.types.unique_gift_model.UniqueGiftModel` class
  - Added :code:`is_burned` field to :class:`aiogram.types.unique_gift.UniqueGift` class

  **New Methods:**

  - Added :class:`aiogram.methods.set_my_profile_photo.SetMyProfilePhoto` method - allows bots to set their profile photo
  - Added :class:`aiogram.methods.remove_my_profile_photo.RemoveMyProfilePhoto` method - allows bots to remove their profile photo
  - Added :class:`aiogram.methods.get_user_profile_audios.GetUserProfileAudios` method - retrieves a user's profile audio list
  - Added :meth:`aiogram.types.user.User.get_profile_audios` shortcut - creates a prefilled :class:`aiogram.methods.get_user_profile_audios.GetUserProfileAudios` request with :code:`user_id`

  **New Types:**

  - Added :class:`aiogram.types.chat_owner_left.ChatOwnerLeft` type - describes a service message about the chat owner leaving the chat
  - Added :class:`aiogram.types.chat_owner_changed.ChatOwnerChanged` type - describes a service message about an ownership change in the chat
  - Added :class:`aiogram.types.video_quality.VideoQuality` type - describes available video quality options
  - Added :class:`aiogram.types.user_profile_audios.UserProfileAudios` type - represents the collection of audios displayed on a user's profile

  `#1761 <https://github.com/aiogram/aiogram/issues/1761>`_


Bugfixes
--------

- Fixed scene handling for ``channel_post`` and ``edited_channel_post`` when Scenes are registered but FSM state is unavailable, and added channel-scoped FSM context support for ``CHAT``/``CHAT_TOPIC`` strategies.
  `#1743 <https://github.com/aiogram/aiogram/issues/1743>`_


Misc
----

- Migrated from Black and isort to Ruff for code formatting and linting, a modern, blazingly fast formatter and linter written in Rust.

  Enabled additional ruff rule sets.

  **For end users:**

  No changes required. This is purely a development tooling change that doesn't affect the library API or behavior.

  **For contributors:**

  - Use ``make reformat`` or ``uv run ruff format`` to format code (replaces ``black`` and ``isort``)
  - Use ``make lint`` to check code quality (now includes formatting, linting, and type checking)
  - Pre-commit hooks automatically updated to use ``ruff`` and ``ruff-format``
  - CI/CD pipelines updated to use ruff in GitHub Actions workflows

  **Benefits:**

  - 10-100x faster formatting and linting compared to Black + isort + flake8
  - Single tool for formatting, import sorting, and linting
  - More comprehensive code quality checks out of the box
  - Auto-fixes for many common issues (33 issues auto-fixed during migration)
  - Better integration with modern Python development workflows

  This change improves the developer experience and code quality while maintaining the same code style standards.
  `#1750 <https://github.com/aiogram/aiogram/issues/1750>`_


3.24.0 (2026-01-02)
====================

Features
--------

- Added full support for Telegram Bot API 9.3

  **Topics in Private Chats**

  Bot API 9.3 introduces forum topics functionality for private chats:

  - Added new ``sendMessageDraft`` method for streaming partial messages while being generated (requires forum topic mode enabled)
  - Added ``has_topics_enabled`` field to the ``User`` class to determine if forum topic mode is enabled in private chats
  - Added ``message_thread_id`` and ``is_topic_message`` fields to the ``Message`` class for private chat topic support
  - Added ``message_thread_id`` parameter support to messaging methods: ``sendMessage``, ``sendPhoto``, ``sendVideo``, ``sendAnimation``, ``sendAudio``, ``sendDocument``, ``sendPaidMedia``, ``sendSticker``, ``sendVideoNote``, ``sendVoice``, ``sendLocation``, ``sendVenue``, ``sendContact``, ``sendPoll``, ``sendDice``, ``sendInvoice``, ``sendGame``, ``sendMediaGroup``, ``copyMessage``, ``copyMessages``, ``forwardMessage``, ``forwardMessages``
  - Updated ``sendChatAction`` to support ``message_thread_id`` parameter in private chats
  - Updated ``editForumTopic``, ``deleteForumTopic``, ``unpinAllForumTopicMessages`` methods to manage private chat topics
  - Added ``is_name_implicit`` field to ``ForumTopic`` class

  **Gifts System Enhancements**

  Enhanced gifts functionality with new methods and extended capabilities:

  - Added ``getUserGifts`` method to retrieve gifts owned and hosted by a user
  - Added ``getChatGifts`` method to retrieve gifts owned by a chat
  - Updated ``UniqueGiftInfo`` class: replaced ``last_resale_star_count`` with ``last_resale_currency`` and ``last_resale_amount`` fields, added "gifted_upgrade" and "offer" as origin values
  - Updated ``getBusinessAccountGifts`` method: replaced ``exclude_limited`` parameter with ``exclude_limited_upgradable`` and ``exclude_limited_non_upgradable``, added ``exclude_from_blockchain`` parameter
  - Added new fields to ``Gift`` class: ``personal_total_count``, ``personal_remaining_count``, ``is_premium``, ``has_colors``, ``unique_gift_variant_count``, ``gift_background``
  - Added new fields to ``UniqueGift`` class: ``gift_id``, ``is_from_blockchain``, ``is_premium``, ``colors``
  - Added new fields to gift info classes: ``is_upgrade_separate``, ``unique_gift_number``
  - Added ``gift_upgrade_sent`` field to the ``Message`` class
  - Added ``gifts_from_channels`` field to the ``AcceptedGiftTypes`` class
  - Added new ``UniqueGiftColors`` class for color schemes in user names and link previews
  - Added new ``GiftBackground`` class for gift background styling

  **Business Accounts & Stories**

  - Added ``repostStory`` method to enable reposting stories across managed business accounts

  **Miscellaneous Updates**

  - Bots can now disable main usernames and set ``can_restrict_members`` rights in channels
  - Maximum paid media price increased to 25000 Telegram Stars
  - Added new ``UserRating`` class
  - Added ``rating``, ``paid_message_star_count``, ``unique_gift_colors`` fields to the ``ChatFullInfo`` class
  - Added support for ``message_effect_id`` parameter in forward/copy operations
  - Added ``completed_by_chat`` field to the ``ChecklistTask`` class
  `#1747 <https://github.com/aiogram/aiogram/issues/1747>`_


Bugfixes
--------

- Fixed I18n initialization with relative path
  `#1740 <https://github.com/aiogram/aiogram/issues/1740>`_
- Fixed dependency injection for arguments that have "ForwardRef" annotations in Py3.14+
  since `inspect.getfullargspec(callback)` can't process callback if it's arguments have "ForwardRef" annotations
  `#1741 <https://github.com/aiogram/aiogram/issues/1741>`_


Misc
----

- Migrated from ``hatch`` to ``uv`` for dependency management and development workflows.

  This change improves developer experience with significantly faster dependency resolution (10-100x faster than pip), automatic virtual environment management, and reproducible builds through lockfile support.

  **What changed for contributors:**

  - Install dependencies with ``uv sync --all-extras --group dev --group test`` instead of ``pip install -e .[dev,test,docs]``
  - Run commands with ``uv run`` prefix (e.g., ``uv run pytest``, ``uv run black``)
  - All Makefile commands now use ``uv`` internally (``make install``, ``make test``, ``make lint``, etc.)
  - Version bumping now uses a custom ``scripts/bump_version.py`` script instead of ``hatch version``

  **What stayed the same:**

  - Build backend remains ``hatchling`` (no changes to package building)
  - Dynamic version reading from ``aiogram/__meta__.py`` still works
  - All GitHub Actions CI/CD workflows updated to use ``uv``
  - ReadTheDocs builds continue to work without changes
  - Development dependencies (``dev``, ``test``) moved to ``[dependency-groups]`` section
  - Documentation dependencies (``docs``) remain in ``[project.optional-dependencies]`` for compatibility

  Contributors can use either the traditional ``pip``/``venv`` workflow or the new ``uv`` workflow - both are documented in the contributing guide.
  `#1748 <https://github.com/aiogram/aiogram/issues/1748>`_
- Updated type hints in the codebase to Python 3.10+ style unions and optionals.
  `#1749 <https://github.com/aiogram/aiogram/issues/1749>`_


3.23.0 (2025-12-07)
====================

Features
--------

- This PR updates the codebase to support Python 3.14.

  - Updated project dep `aiohttp`
  - Updated development deps
  - Fixed tests to support Py3.14
  - Refactored `uvloop` using due to deprecation of `asyncio.set_event_loop_police`
  `#1730 <https://github.com/aiogram/aiogram/issues/1730>`_


Deprecations and Removals
-------------------------

- This PR updates the codebase following the end of life for Python 3.9.

  Reference: https://devguide.python.org/versions/

  - Updated type annotations to Python 3.10+ style, replacing deprecated ``List``, ``Set``, etc., with built-in ``list``, ``set``, and related types.
  - Refactored code by simplifying nested ``if`` expressions.
  - Updated several dependencies, including security-related upgrades.
  `#1726 <https://github.com/aiogram/aiogram/issues/1726>`_


Misc
----

- Updated pydantic to 2.12, which supports Python 3.14
  `#1729 <https://github.com/aiogram/aiogram/issues/1729>`_
- Temporary silents warn when `uvloop` uses deprecated `asyncio.iscoroutinefunction` function in py3.14+ in tests
  `#1739 <https://github.com/aiogram/aiogram/issues/1739>`_


3.22.0 (2025-08-17)
====================

Features
--------

- Support validating init data using only bot id.
  `#1715 <https://github.com/aiogram/aiogram/issues/1715>`_
- Added full support for the `Bot API 9.2 <https://core.telegram.org/bots/api-changelog#august-15-2025>`_:

  **Direct Messages in Channels**

  - Added the field :code:`is_direct_messages` to the classes :class:`aiogram.types.chat.Chat` and :class:`aiogram.types.chat_full_info.ChatFullInfo`, indicating whether the chat is a direct messages chat.
  - Added the field :code:`parent_chat` to the class :class:`aiogram.types.chat_full_info.ChatFullInfo`, describing the parent channel for direct messages chats.
  - Added the class :class:`aiogram.types.direct_messages_topic.DirectMessagesTopic` representing a direct messages topic.
  - Added the field :code:`direct_messages_topic` to the class :class:`aiogram.types.message.Message`, describing the direct messages topic associated with a message.
  - Added the parameter :code:`direct_messages_topic_id` to multiple sending methods for directing messages to specific direct message topics.

  **Suggested Posts**

  - Added the class :class:`aiogram.types.suggested_post_parameters.SuggestedPostParameters` representing parameters for suggested posts.
  - Added the parameter :code:`suggested_post_parameters` to various sending methods, allowing bots to create suggested posts for channel approval.
  - Added the method :class:`aiogram.methods.approve_suggested_post.ApproveSuggestedPost`, allowing bots to approve suggested posts in direct messages chats.
  - Added the method :class:`aiogram.methods.decline_suggested_post.DeclineSuggestedPost`, allowing bots to decline suggested posts in direct messages chats.
  - Added the field :code:`can_manage_direct_messages` to administrator-related classes :class:`aiogram.types.chat_administrator_rights.ChatAdministratorRights` and :class:`aiogram.types.chat_member_administrator.ChatMemberAdministrator`.
  - Added the class :class:`aiogram.types.suggested_post_info.SuggestedPostInfo` representing information about a suggested post.
  - Added the class :class:`aiogram.types.suggested_post_price.SuggestedPostPrice` representing the price for a suggested post.
  - Added service message classes for suggested post events:

    - :class:`aiogram.types.suggested_post_approved.SuggestedPostApproved` and the field :code:`suggested_post_approved` to :class:`aiogram.types.message.Message`
    - :class:`aiogram.types.suggested_post_approval_failed.SuggestedPostApprovalFailed` and the field :code:`suggested_post_approval_failed` to :class:`aiogram.types.message.Message`
    - :class:`aiogram.types.suggested_post_declined.SuggestedPostDeclined` and the field :code:`suggested_post_declined` to :class:`aiogram.types.message.Message`
    - :class:`aiogram.types.suggested_post_paid.SuggestedPostPaid` and the field :code:`suggested_post_paid` to :class:`aiogram.types.message.Message`
    - :class:`aiogram.types.suggested_post_refunded.SuggestedPostRefunded` and the field :code:`suggested_post_refunded` to :class:`aiogram.types.message.Message`

  **Enhanced Checklists**

  - Added the field :code:`checklist_task_id` to the class :class:`aiogram.types.reply_parameters.ReplyParameters`, allowing replies to specific checklist tasks.
  - Added the field :code:`reply_to_checklist_task_id` to the class :class:`aiogram.types.message.Message`, indicating which checklist task a message is replying to.

  **Gifts Improvements**

  - Added the field :code:`publisher_chat` to the classes :class:`aiogram.types.gift.Gift` and :class:`aiogram.types.unique_gift.UniqueGift`, describing the chat that published the gift.

  **Additional Features**

  - Added the field :code:`is_paid_post` to the class :class:`aiogram.types.message.Message`, indicating whether a message is a paid post.
  `#1720 <https://github.com/aiogram/aiogram/issues/1720>`_


Bugfixes
--------

- Use `hmac.compare_digest` for validating WebApp data to prevent timing attacks.
  `#1709 <https://github.com/aiogram/aiogram/issues/1709>`_


Misc
----

- Migrated `MongoStorage` from relying on deprecated `motor` package to using new async `PyMongo`. To use mongo storage with new async `PyMongo`, you need to install the `PyMongo` package instead of `motor` and just substitute deprecated `MongoStorage` with `PyMongoStorage` class, no other action needed.
  `#1705 <https://github.com/aiogram/aiogram/issues/1705>`_


3.21.0 (2025-07-05)
====================

Features
--------

- Refactor methods input types to calm down MyPy. #1682

  `Dict[str, Any]` is replaced with `Mapping[str, Any]` in the following methods:

  - `FSMContext.set_data`
  - `FSMContext.update_data`
  - `BaseStorage.set_data`
  - `BaseStorage.update_data`
  - `BaseStorage's child methods`
  - `SceneWizard.set_data`
  - `SceneWizard.update_data`
  `#1683 <https://github.com/aiogram/aiogram/issues/1683>`_
- Add support for `State` type in scenes methods like `goto`, `enter`, `get`
  `#1685 <https://github.com/aiogram/aiogram/issues/1685>`_
- Added full support for the `Bot API 9.1 <https://core.telegram.org/bots/api-changelog#july-3-2025>`_:

  **Checklists**

  - Added the class :class:`aiogram.types.checklist_task.ChecklistTask` representing a task in a checklist.
  - Added the class :class:`aiogram.types.checklist.Checklist` representing a checklist.
  - Added the class :class:`aiogram.types.input_checklist_task.InputChecklistTask` representing a task to add to a checklist.
  - Added the class :class:`aiogram.types.input_checklist.InputChecklist` representing a checklist to create.
  - Added the field :code:`checklist` to the classes :class:`aiogram.types.message.Message` and :class:`aiogram.types.external_reply_info.ExternalReplyInfo`, describing a checklist in a message.
  - Added the class :class:`aiogram.types.checklist_tasks_done.ChecklistTasksDone` and the field :code:`checklist_tasks_done` to the class :class:`aiogram.types.message.Message`, describing a service message about status changes for tasks in a checklist (i.e., marked as done/not done).
  - Added the class :class:`aiogram.types.checklist_tasks_added.ChecklistTasksAdded` and the field :code:`checklist_tasks_added` to the class :class:`aiogram.types.message.Message`, describing a service message about the addition of new tasks to a checklist.
  - Added the method :class:`aiogram.methods.send_checklist.SendChecklist`, allowing bots to send a checklist on behalf of a business account.
  - Added the method :class:`aiogram.methods.edit_message_checklist.EditMessageChecklist`, allowing bots to edit a checklist on behalf of a business account.

  **Gifts**

  - Added the field :code:`next_transfer_date` to the classes :class:`aiogram.types.owned_gift_unique.OwnedGiftUnique` and :class:`aiogram.types.unique_gift_info.UniqueGiftInfo`.
  - Added the field :code:`last_resale_star_count` to the class :class:`aiogram.types.unique_gift_info.UniqueGiftInfo`.
  - Added "resale" as the possible value of the field :code:`origin` in the class :class:`aiogram.types.unique_gift_info.UniqueGiftInfo`.

  **General**

  - Increased the maximum number of options in a poll to 12.
  - Added the method :class:`aiogram.methods.get_my_star_balance.GetMyStarBalance`, allowing bots to get their current balance of Telegram Stars.
  - Added the class :class:`aiogram.types.direct_message_price_changed.DirectMessagePriceChanged` and the field :code:`direct_message_price_changed` to the class :class:`aiogram.types.message.Message`, describing a service message about a price change for direct messages sent to the channel chat.
  `#1704 <https://github.com/aiogram/aiogram/issues/1704>`_


Bugfixes
--------

- Fixed an issue where the scene entry handler (:code:`enter`) was not receiving data
  passed to the context by middleware, which could result in a :code:`TypeError`.

  Also updated the documentation to clarify how to enter the scene.
  `#1672 <https://github.com/aiogram/aiogram/issues/1672>`_
- Correctly pass error message in TelegramMigrateToChat.
  `#1694 <https://github.com/aiogram/aiogram/issues/1694>`_


Improved Documentation
----------------------

- Added documentation for changing state of another user in FSM
  `#1633 <https://github.com/aiogram/aiogram/issues/1633>`_


Misc
----

- Fixed MyPy [return-value] error in `InlineKeyboardBuilder().as_markup()`.
  `as_markup` method now overloads parent class method and uses `super()`, to call parent's
  `as_markup` method.
  Also added correct type hint to `as_markup`'s return in `InlineKeyboardBuilder` and
  `ReplyKeyboardBuilder` classes.
  `#1677 <https://github.com/aiogram/aiogram/issues/1677>`_
- Changed Babel's pinned version from minor to major.
  `#1681 <https://github.com/aiogram/aiogram/issues/1681>`_
- Increased max :code:`aiohttp` version support from “<3.12” to “<3.13”
  `#1700 <https://github.com/aiogram/aiogram/issues/1700>`_


3.20.0 (2025-04-14)
====================

Features
--------

- Add different shortcut methods for ``aiogram.utils.formatting.Text.as_kwargs()``
  `#1657 <https://github.com/aiogram/aiogram/issues/1657>`_
- Added full support for the `Bot API 9.0 <https://core.telegram.org/bots/api-changelog#april-11-2025>`_:

  **Business Accounts**

  - Added the class :class:`aiogram.types.business_bot_rights.BusinessBotRights` and replaced
    the field :code:`can_reply` with the field :code:`rights` of the type
    :class:`aiogram.types.business_bot_rights.BusinessBotRights` in the class
    :class:`aiogram.types.business_connection.BusinessConnection`.
  - Added the method :class:`aiogram.methods.read_business_message.ReadBusinessMessage`,
    allowing bots to mark incoming messages as read on behalf of a business account.
  - Added the method :class:`aiogram.methods.delete_business_messages.DeleteBusinessMessages`,
    allowing bots to delete messages on behalf of a business account.
  - Added the method :class:`aiogram.methods.set_business_account_name.SetBusinessAccountName`,
    allowing bots to change the first and last name of a managed business account.
  - Added the method :class:`aiogram.methods.set_business_account_username.SetBusinessAccountUsername`,
    allowing bots to change the username of a managed business account.
  - Added the method :class:`aiogram.methods.set_business_account_bio.SetBusinessAccountBio`,
    allowing bots to change the bio of a managed business account.
  - Added the class :class:`aiogram.types.input_profile_photo.InputProfilePhoto`,
    describing a profile photo to be set.
  - Added the methods :class:`aiogram.methods.set_business_account_profile_photo.SetBusinessAccountProfilePhoto`
    and :class:`aiogram.methods.remove_business_account_profile_photo.RemoveBusinessAccountProfilePhoto`,
    allowing bots to change the profile photo of a managed business account.
  - Added the method :class:`aiogram.methods.set_business_account_gift_settings.SetBusinessAccountGiftSettings`,
    allowing bots to change the privacy settings pertaining to incoming gifts in a managed business account.
  - Added the class :class:`aiogram.types.star_amount.StarAmount` and the method
    :class:`aiogram.methods.get_business_account_star_balance.GetBusinessAccountStarBalance`,
    allowing bots to check the current Telegram Star balance of a managed business account.
  - Added the method :class:`aiogram.methods.transfer_business_account_stars.TransferBusinessAccountStars`,
    allowing bots to transfer Telegram Stars from the balance of a managed business account to their own balance
    for withdrawal.
  - Added the classes :class:`aiogram.types.owned_gift_regular.OwnedGiftRegular`,
    :class:`aiogram.types.owned_gift_unique.OwnedGiftUnique`, :class:`aiogram.types.owned_gifts.OwnedGifts`
    and the method :class:`aiogram.methods.get_business_account_gifts.GetBusinessAccountGifts`,
    allowing bots to fetch the list of gifts owned by a managed business account.
  - Added the method :class:`aiogram.methods.convert_gift_to_stars.ConvertGiftToStars`,
    allowing bots to convert gifts received by a managed business account to Telegram Stars.
  - Added the method :class:`aiogram.methods.upgrade_gift.UpgradeGift`,
    allowing bots to upgrade regular gifts received by a managed business account to unique gifts.
  - Added the method :class:`aiogram.methods.transfer_gift.TransferGift`,
    allowing bots to transfer unique gifts owned by a managed business account.
  - Added the classes :class:`aiogram.types.input_story_content_photo.InputStoryContentPhoto`
    and :class:`aiogram.types.input_story_content_video.InputStoryContentVideo`
    representing the content of a story to post.
  - Added the classes :class:`aiogram.types.story_area.StoryArea`,
    :class:`aiogram.types.story_area_position.StoryAreaPosition`,
    :class:`aiogram.types.location_address.LocationAddress`,
    :class:`aiogram.types.story_area_type_location.StoryAreaTypeLocation`,
    :class:`aiogram.types.story_area_type_suggested_reaction.StoryAreaTypeSuggestedReaction`,
    :class:`aiogram.types.story_area_type_link.StoryAreaTypeLink`,
    :class:`aiogram.types.story_area_type_weather.StoryAreaTypeWeather`
    and :class:`aiogram.types.story_area_type_unique_gift.StoryAreaTypeUniqueGift`,
    describing clickable active areas on stories.
  - Added the methods :class:`aiogram.methods.post_story.PostStory`,
    :class:`aiogram.methods.edit_story.EditStory`
    and :class:`aiogram.methods.delete_story.DeleteStory`,
    allowing bots to post, edit and delete stories on behalf of a managed business account.

  **Mini Apps**

  - Added the field :code:`DeviceStorage`, allowing Mini Apps to use persistent
    local storage on the user's device.
  - Added the field :code:`SecureStorage`, allowing Mini Apps to use a secure local
    storage on the user's device for sensitive data.

  **Gifts**

  - Added the classes :class:`aiogram.types.unique_gift_model.UniqueGiftModel`,
    :class:`aiogram.types.unique_gift_symbol.UniqueGiftSymbol`,
    :class:`aiogram.types.unique_gift_backdrop_colors.UniqueGiftBackdropColors`,
    and :class:`aiogram.types.unique_gift_backdrop.UniqueGiftBackdrop`
    to describe the properties of a unique gift.
  - Added the class :class:`aiogram.types.unique_gift.UniqueGift` describing
    a gift that was upgraded to a unique one.
  - Added the class :class:`aiogram.types.accepted_gift_types.AcceptedGiftTypes`
    describing the types of gifts that are accepted by a user or a chat.
  - Replaced the field :code:`can_send_gift` with the field :code:`accepted_gift_types`
    of the type :class:`aiogram.types.accepted_gift_types.AcceptedGiftTypes`
    in the class :class:`aiogram.types.chat_full_info.ChatFullInfo`.
  - Added the class :class:`aiogram.types.gift_info.GiftInfo` and the field :code:`gift`
    to the class :class:`aiogram.types.message.Message`,
    describing a service message about a regular gift that was sent or received.
  - Added the class :class:`aiogram.types.unique_gift_info.UniqueGiftInfo`
    and the field :code:`unique_gift` to the class :class:`aiogram.types.message.Message`,
    describing a service message about a unique gift that was sent or received.

  **Telegram Premium**

  - Added the method :class:`aiogram.methods.gift_premium_subscription.GiftPremiumSubscription`,
    allowing bots to gift a user a Telegram Premium subscription paid in Telegram Stars.
  - Added the field :code:`premium_subscription_duration` to the class
    :class:`aiogram.types.transaction_partner_user.TransactionPartnerUser`
  for transactions involving a Telegram Premium subscription purchased by the bot.
  - Added the field :code:`transaction_type` to the class
    :class:`aiogram.types.transaction_partner_user.TransactionPartnerUser`,
    simplifying the differentiation and processing of all transaction types.

  **General**

  - Increased the maximum price for paid media to 10000 Telegram Stars.
  - Increased the maximum price for a subscription period to 10000 Telegram Stars.
  - Added the class :class:`aiogram.types.paid_message_price_changed.PaidMessagePriceChanged`
    and the field :code:`paid_message_price_changed` to the class
    :class:`aiogram.types.message.Message`, describing a service message about a price change
    for paid messages sent to the chat.
  - Added the field :code:`paid_star_count` to the class :class:`aiogram.types.message.Message`,
    containing the number of Telegram Stars that were paid to send the message.
  `#1671 <https://github.com/aiogram/aiogram/issues/1671>`_


Bugfixes
--------

- Fix memory exhaustion in polling mode with concurrent updates.

  Added a semaphore-based solution to limit the number of concurrent tasks when using :code:`handle_as_tasks=True` in polling mode.
  This prevents Out of Memory (OOM) errors in memory-limited containers when there's a large queue of updates to process.
  You can now control the maximum number of concurrent updates with the new :code:`tasks_concurrency_limit`
  parameter in :code:`start_polling()` and :code:`run_polling()` methods.
  `#1658 <https://github.com/aiogram/aiogram/issues/1658>`_
- Fix empty response into webhook.

  We need to return something “empty”, and “empty” form doesn’t work since
  it’s sending only “end” boundary w/o “start”.

  An empty formdata should look smth like this for Telegram to understand:

  ::

     --webhookBoundaryvsF_aMHhspPjfOq7O0JNRg
     --webhookBoundaryvsF_aMHhspPjfOq7O0JNRg--

  But aiohttp sends only the ending boundary:

  ::

     --webhookBoundaryvsF_aMHhspPjfOq7O0JNRg--

  Such response doesn't suit Telegram servers.

  The fix replaces empty response with empty JSON response:

  ::

     {}
  `#1664 <https://github.com/aiogram/aiogram/issues/1664>`_


Improved Documentation
----------------------

- Fixed broken code block formatting in ``router.rst`` caused by incorrect indentation of directive options.
  `#1666 <https://github.com/aiogram/aiogram/issues/1666>`_


Misc
----

- Bump pydantic upper bound from <2.11 to <2.12.
  Upgrading `pydantic` to version 2.11 significantly reduces resource consumption, more details on the `pydantic blog post <https://pydantic.dev/articles/pydantic-v2-11-release>`_
  `#1659 <https://github.com/aiogram/aiogram/issues/1659>`_
- Replaced ```loop.run_in_executor``` with ```asyncio.to_thread``` for improved readability and consistency.
  `#1661 <https://github.com/aiogram/aiogram/issues/1661>`_


3.19.0 (2025-03-19)
====================

Features
--------

- Added TypedDict definitions for middleware context data to the dispatcher dependency injection docs.

  So, now you can use :class:`aiogram.dispatcher.middleware.data.MiddlewareData` directly or
  extend it with your own data in the middlewares.
  `#1637 <https://github.com/aiogram/aiogram/issues/1637>`_
- Added new method :func:`aiogram.utils.deep_linking.create_startapp_link` to deep-linking module
  for creating "startapp" deep links.
  See also https://core.telegram.org/api/links#main-mini-app-links and https://core.telegram.org/api/links#direct-mini-app-links
  `#1648 <https://github.com/aiogram/aiogram/issues/1648>`_, `#1651 <https://github.com/aiogram/aiogram/issues/1651>`_


Bugfixes
--------

- Fixed handling of default empty string ("") in CallbackData filter
  `#1493 <https://github.com/aiogram/aiogram/issues/1493>`_
- Resolved incorrect ordering of registered handlers in the :class:`aiogram.fsm.scene.Scene`
  object caused by :code:`inspect.getmembers` returning sorted members.
  Handlers are now registered in the order of their definition within the class,
  ensuring proper execution sequence, especially when handling filters with different
  levels of specificity.

  For backward compatibility, the old behavior can be restored by setting the
  :code:`attrs_resolver=inspect_members_resolver` parameter in the :class:`aiogram.fsm.scene.Scene`:

  .. code-block:: python

      from aiogram.utils.class_attrs_resolver import inspect_members_resolver


      class MyScene(Scene, attrs_resolver=inspect_members_resolver):

  In this case, the handlers will be registered in the order returned by :code:`inspect.getmembers`.

  By default, the :code:`attrs_resolver` parameter is set to :code:`get_sorted_mro_attrs_resolver` now,
  so you **don't need** to specify it explicitly.
  `#1641 <https://github.com/aiogram/aiogram/issues/1641>`_


Improved Documentation
----------------------

- Updated 🇺🇦Ukrainian docs translation
  `#1650 <https://github.com/aiogram/aiogram/issues/1650>`_


Misc
----

- Introduce Union types for streamlined type handling.

  Implemented Union types across various modules to consolidate and simplify type annotations.
  This change replaces repetitive union declarations with reusable Union aliases,
  improving code readability and maintainability.
  `#1592 <https://github.com/aiogram/aiogram/issues/1592>`_


3.18.0 (2025-02-16)
====================

Features
--------

- Added full support for the `Bot API 8.3 <https://core.telegram.org/bots/api-changelog#february-12-2025>`_:

  - Added the parameter :code:`chat_id` to the method :class:`aiogram.methods.send_gift.SendGift`, allowing bots to send gifts to channel chats.
  - Added the field :code:`can_send_gift` to the class :class:`aiogram.types.chat_full_info.ChatFullInfo`.
  - Added the class :class:`aiogram.types.transaction_partner_chat.TransactionPartnerChat` describing transactions with chats.
  - Added the fields :code:`cover` and :code:`start_timestamp` to the class :class:`aiogram.types.video.Video`, containing a message-specific cover and a start timestamp for the video.
  - Added the parameters :code:`cover` and :code:`start_timestamp` to the method :class:`aiogram.methods.send_video.SendVideo`, allowing bots to specify a cover and a start timestamp for the videos they send.
  - Added the fields :code:`cover` and :code:`start_timestamp` to the classes :class:`aiogram.types.input_media_video.InputMediaVideo` and :class:`aiogram.types.input_paid_media_video.InputPaidMediaVideo`, allowing bots to edit video covers and start timestamps, and specify them for videos in albums and paid media.
  - Added the parameter :code:`video_start_timestamp` to the methods :class:`aiogram.methods.forward_message.ForwardMessage` and :class:`aiogram.methods.copy_message.CopyMessage`, allowing bots to change the start timestamp for forwarded and copied videos.
  - Allowed adding reactions to most types of service messages.
  `#1638 <https://github.com/aiogram/aiogram/issues/1638>`_


Bugfixes
--------

- Fixed endless loop while adding buttons to the :code:`KeyboardBuilder`.
  `#1595 <https://github.com/aiogram/aiogram/issues/1595>`_
- Change the :code:`Downloadable` protocol to be non-writable to shut up type checking that checks code that uses the :code:`bot.download(...)` method
  `#1628 <https://github.com/aiogram/aiogram/issues/1628>`_
- Fix the regex pattern that finds the "bad characters" for deeplink payload.
  `#1630 <https://github.com/aiogram/aiogram/issues/1630>`_


Improved Documentation
----------------------

- Update :code:`data: Dict[Any, str]` to :code:`data: Dict[str, Any]`
  `#1634 <https://github.com/aiogram/aiogram/issues/1634>`_
- Fix small typo in the Scenes documentation
  `#1640 <https://github.com/aiogram/aiogram/issues/1640>`_

Misc
----

- Removed redundant :code:`Path` to :code:`str` convertion on file download.
  `#1612 <https://github.com/aiogram/aiogram/issues/1612>`_
- Increased max :code:`redis` version support from “<5.1.0” to “<5.3.0”
  `#1631 <https://github.com/aiogram/aiogram/issues/1631>`_


3.17.0 (2025-01-02)
====================

Features
--------

- Added full support of the `Bot API 8.2 <https://core.telegram.org/bots/api-changelog#january-1-2025>`_

  - Added the methods :class:`aiogram.methods.verify_user.VerifyUser`, :class:`aiogram.methods.verify_chat.VerifyChat`, :class:`aiogram.methods.remove_user_verification.RemoveUserVerification` and :class:`aiogram.methods.remove_chat_verification.RemoveChatVerification`, allowing bots to manage verifications on behalf of an organization.
  - Added the field :code:`upgrade_star_count` to the class :class:`aiogram.types.gift.Gift`.
  - Added the parameter :code:`pay_for_upgrade` to the method :class:`aiogram.methods.send_gift.SendGift`.
  - Removed the field :code:`hide_url` from the class :class:`aiogram.types.inline_query_result_article.InlineQueryResultArticle`. Pass an empty string as :code:`url` instead.
  `#1623 <https://github.com/aiogram/aiogram/issues/1623>`_


3.16.0 (2024-12-21)
====================

Features
--------

- Added full support of `Bot API 8.1 <https://core.telegram.org/bots/api-changelog#december-4-2024>`_:

  - Added the field :code:`nanostar_amount` to the class :class:`aiogram.types.star_transaction.StarTransaction`.
  - Added the class :class:`aiogram.types.transaction_partner_affiliate_program.TransactionPartnerAffiliateProgram` for transactions pertaining to incoming affiliate commissions.
  - Added the class :class:`aiogram.types.affiliate_info.AffiliateInfo` and the field :code:`affiliate` to the class :class:`aiogram.types.transaction_partner_user.TransactionPartnerUser`, allowing bots to identify the relevant affiliate in transactions with an affiliate commission.
  `#1617 <https://github.com/aiogram/aiogram/issues/1617>`_


Bugfixes
--------

- Corrected the exception text of `aiogram.methods.base.TelegramMethod.__await__` method.
  `#1616 <https://github.com/aiogram/aiogram/issues/1616>`_


Misc
----

- Increased max :code:`pydantic` version support from “<2.10” to “<2.11”
  `#1607 <https://github.com/aiogram/aiogram/issues/1607>`_
- Fixed closing tag for :code:`tg-emoji` in the :class:`aiogram.utils.text_decoration.HtmlDecoration`: use the same constant as for tag opening
  `#1608 <https://github.com/aiogram/aiogram/issues/1608>`_
- Increased max :code:`aiohttp` version support from “<3.11” to “<3.12”
  `#1615 <https://github.com/aiogram/aiogram/issues/1615>`_


3.15.0 (2024-11-17)
====================

Features
--------

- Added full support for `Bot API 8.0 <https://core.telegram.org/bots/api-changelog#november-17-2024>`_

  - Added the parameter :code:`subscription_period` to the method
    :class:`aiogram.methods.create_invoice_link.CreateInvoiceLink`
    to support the creation of links that are billed periodically.
  - Added the parameter :code:`business_connection_id` to the method
    :class:`aiogram.methods.create_invoice_link.CreateInvoiceLink`
    to support the creation of invoice links on behalf of business accounts.
  - Added the fields :code:`subscription_expiration_date`,
    :code:`is_recurring` and :code:`is_first_recurring` to the class
    :class:`aiogram.types.successful_payment.SuccessfulPayment`.
  - Added the method :class:`aiogram.methods.edit_user_star_subscription.EditUserStarSubscription`.
  - Added the field :code:`subscription_period` to the class
    :class:`aiogram.types.transaction_partner_user.TransactionPartnerUser`.
  - Added the method :class:`aiogram.methods.set_user_emoji_status.SetUserEmojiStatus`.
    The user must allow the bot to manage their emoji status.
  - Added the class :class:`aiogram.types.prepared_inline_message.PreparedInlineMessage`
    and the method :class:`aiogram.methods.save_prepared_inline_message.SavePreparedInlineMessage`,
    allowing bots to suggest users send a specific message from a Mini App via the method
    :class:`aiogram.methods.share_message.ShareMessage`.
  - Added the classes :class:`aiogram.types.gift.Gift` and :class:`aiogram.types.gifts.Gifts`
    and the method :class:`aiogram.methods.get_available_gifts.GetAvailableGifts`,
    allowing bots to get all gifts available for sending.
  - Added the field :code:`gift` to the class
    :class:`aiogram.types.transaction_partner_user.TransactionPartnerUser`.
  `#1606 <https://github.com/aiogram/aiogram/issues/1606>`_


3.14.0 (2024-11-02)
====================

Misc
----

- Checked compatibility with Python 3.13 (added to the CI/CD processes),
  so now aiogram is totally compatible with it.

  Dropped compatibility with Python 3.8 due to this version being `EOL <https://devguide.python.org/versions/>`_.

  .. warning::

    In some cases you will need to have the installed compiler (Rust or C++)
    to install some of the dependencies to compile packages from source on `pip install` command.

    - If you are using Windows, you will need to have the `Visual Studio <https://visualstudio.microsoft.com/visual-cpp-build-tools/>`_ installed.
    - If you are using Linux, you will need to have the `build-essential` package installed.
    - If you are using macOS, you will need to have the `Xcode <https://developer.apple.com/xcode/>`_ installed.

    When developers of this dependencies will release new versions with precompiled wheels for Windows, Linux and macOS,
    this action will not be necessary anymore until the next version of the Python interpreter.
  `#1589 <https://github.com/aiogram/aiogram/issues/1589>`_
- Added business_connection_id to the :class:`aiogram.types.message.Message` API methods shortcuts.

  Integrated the :code:`business_connection_id` attribute into various message manipulation methods,
  ensuring consistent data handling. This update eliminates the need to pass the
  :code:`business_connection_id` as a parameter,
  instead directly accessing it from the instance attributes.
  `#1586 <https://github.com/aiogram/aiogram/issues/1586>`_

Features
--------

- Add function ``get_value`` to all built-in storage implementations, ``FSMContext`` and ``SceneWizard``
  `#1431 <https://github.com/aiogram/aiogram/issues/1431>`_
- Enhanced the inheritance of handlers and actions in :ref:`Scenes <Scenes>`.
  Refactored to eliminate the copying of previously connected handlers and actions from parent scenes.
  Now, handlers are dynamically rebuilt based on the current class, properly utilizing class inheritance and enabling handler overrides.

  That's mean that you can now override handlers and actions in the child scene, instead of copying and duplicating them.
  `#1583 <https://github.com/aiogram/aiogram/issues/1583>`_
- Added full support of `Bot API 7.11 <https://core.telegram.org/bots/api-changelog#october-31-2024>`_

  - Added the class :class:`aiogram.types.copy_text_button.CopyTextButton`
    and the field :code:`copy_text` in the class
    :class:`aiogram.types.inline_keyboard_button.InlineKeyboardButton`,
    allowing bots to send and receive inline buttons that copy arbitrary text.
  - Added the parameter :code:`allow_paid_broadcast` to the methods
    :class:`aiogram.methods.send_message.SendMessage`,
    :class:`aiogram.methods.send_photo.SendPhoto`,
    :class:`aiogram.methods.send_video.SendVideo`,
    :class:`aiogram.methods.send_animation.SendAnimation`,
    :class:`aiogram.methods.send_audio.SendAudio`,
    :class:`aiogram.methods.send_document.SendDocument`,
    :class:`aiogram.methods.send_paid_media.SendPaidMedia`,
    :class:`aiogram.methods.send_sticker.SendSticker`,
    :class:`aiogram.methods.send_video_note.SendVideoNote`,
    :class:`aiogram.methods.send_voice.SendVoice`,
    :class:`aiogram.methods.send_location.SendLocation`,
    :class:`aiogram.methods.send_venue.SendVenue`,
    :class:`aiogram.methods.send_contact.SendContact`,
    :class:`aiogram.methods.send_poll.SendPoll`,
    :class:`aiogram.methods.send_dice.SendDice`,
    :class:`aiogram.methods.send_invoice.SendInvoice`,
    :class:`aiogram.methods.send_game.SendGame`,
    :class:`aiogram.methods.send_media_group.SendMediaGroup`
    and :class:`aiogram.methods.copy_message.CopyMessage`.
  - Added the class
    :class:`aiogram.types.transaction_partner_telegram_api.TransactionPartnerTelegramApi`
    for transactions related to paid broadcasted messages.
  - Introduced the ability to add media to existing text messages using the method
    :class:`aiogram.methods.edit_message_media.EditMessageMedia`.
  - Added support for hashtag and cashtag entities with a specified chat username
    that opens a search for the relevant tag within the specified chat.
  `#1601 <https://github.com/aiogram/aiogram/issues/1601>`_


Bugfixes
--------

- Fix PytestDeprecationWarning thrown by pytest-asyncio when running the tests
  `#1584 <https://github.com/aiogram/aiogram/issues/1584>`_
- Fixed customized serialization in the :class:`aiogram.filters.callback_data.CallbackData` factory.

  From now UUID will have 32 bytes length instead of 36 bytes (with no `-` separators) in the callback data representation.
  `#1602 <https://github.com/aiogram/aiogram/issues/1602>`_


Improved Documentation
----------------------

- Add missing closing tag for bold.
  `#1599 <https://github.com/aiogram/aiogram/issues/1599>`_


3.13.1 (2024-09-18)
====================

.. warning::

    **Python 3.8 End of Life**: Python 3.8 will reach its end of life (EOL) soon and will no longer
    be supported by aiogram in the next releases (1-2 months ETA).

    Please upgrade to a newer version of Python to ensure compatibility and receive future updates.

Misc
----

- Increase max pydantic version support "<2.9" -> "<2.10" (only For Python >=3.9)
  `#1576 <https://github.com/aiogram/aiogram/issues/1576>`_
- Bump aiofiles version upper bound to <24.2
  `#1577 <https://github.com/aiogram/aiogram/issues/1577>`_


Bugfixes
--------

- Fixed `Default` object annotation resolution using `pydantic`
  `#1579 <https://github.com/aiogram/aiogram/issues/1579>`_


3.13.0 (2024-09-08)
====================

Features
--------

- - Added updates about purchased paid media, represented by the class
    :class:`aiogram.types.paid_media_purchased.PaidMediaPurchased`
    and the field :code:`purchased_paid_media` in the class
    :class:`aiogram.types.update.Update`.
  - Added the ability to specify a payload in
    :class:`aiogram.methods.send_paid_media.SendPaidMedia` that is received back by the bot in
    :class:`aiogram.types.transaction_partner_user.TransactionPartnerUser`
    and :code:`purchased_paid_media` updates.
  - Added the field :code:`prize_star_count` to the classes
    :class:`aiogram.types.giveaway_created.GiveawayCreated`,
    :class:`aiogram.types.giveaway.Giveaway`,
    :class:`aiogram.types.giveaway_winners.GiveawayWinners`
    and :class:`aiogram.types.chat_boost_source_giveaway.ChatBoostSourceGiveaway`.
  - Added the field :code:`is_star_giveaway` to the class
    :class:`aiogram.types.giveaway_completed.GiveawayCompleted`.
  `#1510 <https://github.com/aiogram/aiogram/issues/1510>`_
- Added missing method aliases such as `.answer()`, `.reply()`, and others to `InaccessibleMessage`.
  This change ensures consistency and improves usability by aligning the functionality of `InaccessibleMessage` with the `Message` type.
  `#1574 <https://github.com/aiogram/aiogram/issues/1574>`_


Bugfixes
--------

- Fixed link preview options to use global defaults in various types and methods
  to use global defaults for `link_preview_options`.
  This change ensures consistency and enhances flexibility in handling link preview options
  across different components.
  `#1543 <https://github.com/aiogram/aiogram/issues/1543>`_


3.12.0 (2024-08-16)
====================

Features
--------

- Added **message_thread_id** parameter to **message.get_url()**.
  `#1451 <https://github.com/aiogram/aiogram/issues/1451>`_
- Added getting user from `chat_boost` with source `ChatBoostSourcePremium` in `UserContextMiddleware` for `EventContext`
  `#1474 <https://github.com/aiogram/aiogram/issues/1474>`_
- Added full support of `Bot API 7.8 <https://core.telegram.org/bots/api-changelog#august-14-2024>`_

  - Added the ability to send paid media to any chat.
  - Added the parameter :code:`business_connection_id` to the method
    :class:`aiogram.methods.send_paid_media.SendPaidMedia`,
    allowing bots to send paid media on behalf of a business account.
  - Added the field :code:`paid_media` to the class
    :class:`aiogram.types.transaction_partner_user.TransactionPartnerUser`
    for transactions involving paid media.
  - Added the method
    :class:`aiogram.methods.create_chat_subscription_invite_link.CreateChatSubscriptionInviteLink`,
    allowing bots to create subscription invite links.
  - Added the method
    :class:`aiogram.methods.edit_chat_subscription_invite_link.EditChatSubscriptionInviteLink`,
    allowing bots to edit the name of subscription invite links.
  - Added the field :code:`until_date` to the class
    :class:`aiogram.types.chat_member_member.ChatMemberMember` for members with an active subscription.
  - Added support for paid reactions and the class
    :class:`aiogram.types.reaction_type_paid.ReactionTypePaid`.
  `#1560 <https://github.com/aiogram/aiogram/issues/1560>`_


Misc
----

- Improved performance of StatesGroup
  `#1507 <https://github.com/aiogram/aiogram/issues/1507>`_


3.11.0 (2024-08-09)
====================

Features
--------

- Added full support of `Bot API 7.8 <https://core.telegram.org/bots/api-changelog#july-31-2024>`_

  - Added the field :code:`has_main_web_app` to the class :class:`aiogram.types.user.User`,
    which is returned in the response to :class:`aiogram.methods.get_me.GetMe`.
  - Added the parameter :code:`business_connection_id` to the methods
    :class:`aiogram.methods.pin_chat_message.PinChatMessage`
    and :class:`aiogram.methods.unpin_chat_message.UnpinChatMessage`,
    allowing bots to manage pinned messages on behalf of a business account.
  `#1551 <https://github.com/aiogram/aiogram/issues/1551>`_


Bugfixes
--------

- Fixed URL path in the "Open" button at the "demo/sendMessage" endpoint in the web_app example.
  `#1546 <https://github.com/aiogram/aiogram/issues/1546>`_


Misc
----

- Added method :func:`aiogram.types.message.Message.as_reply_parameters`.
  Replaced usage of the argument :code:`reply_to_message_id` with :code:`reply_parameters`
  in all Message reply methods.
  `#1538 <https://github.com/aiogram/aiogram/issues/1538>`_
- Added `aiohttp v3.10 <https://github.com/aio-libs/aiohttp/releases/tag/v3.10.0>`_ ` support.
  `#1548 <https://github.com/aiogram/aiogram/issues/1548>`_


3.10.0 (2024-07-07)
====================

Features
--------

- Added full support of `Bot API 7.7 <https://core.telegram.org/bots/api-changelog#july-7-2024>`_

  - Added the class :class:`aiogram.types.refunded_payment.RefundedPayment`,
    containing information about a refunded payment.
  - Added the field :code:`refunded_payment` to the class
    :class:`aiogram.types.message.Message`,
    describing a service message about a refunded payment.
  `#1536 <https://github.com/aiogram/aiogram/issues/1536>`_


3.9.0 (2024-07-06)
===================

Features
--------

- Added ChatMember resolution tool and updated 2.x migration guide.
  `#1525 <https://github.com/aiogram/aiogram/issues/1525>`_
- Added full support of `Bot API 7.6 <https://core.telegram.org/bots/api-changelog#july-1-2024>`_

  - Added the classes :class:`aiogram.types.paid_media.PaidMedia`,
      :class:`aiogram.types.paid_media_info.PaidMediaInfo`,
      :class:`aiogram.types.paid_media_preview.PaidMediaPreview`,
      :class:`aiogram.types.paid_media_photo.PaidMediaPhoto`
      and :class:`aiogram.types.paid_media_video.PaidMediaVideo`,
      containing information about paid media.
  - Added the method :class:`aiogram.methods.send_paid_media.SendPaidMedia`
      and the classes :class:`aiogram.types.input_paid_media.InputPaidMedia`,
      :class:`aiogram.types.input_paid_media_photo.InputPaidMediaPhoto`
      and :class:`aiogram.types.input_paid_media_video.InputPaidMediaVideo`,
      to support sending paid media.
  - Documented that the methods :class:`aiogram.methods.copy_message.CopyMessage`
      and :class:`aiogram.methods.copy_messages.CopyMessages` cannot be used to copy paid media.
  - Added the field :code:`can_send_paid_media` to the class
      :class:`aiogram.types.chat_full_info.ChatFullInfo`.
  - Added the field :code:`paid_media` to the classes
      :class:`aiogram.types.message.Message` and
      :class:`aiogram.types.external_reply_info.ExternalReplyInfo`.
  - Added the class
      :class:`aiogram.types.transaction_partner_telegram_ads.TransactionPartnerTelegramAds`,
      containing information about Telegram Star transactions involving the Telegram Ads Platform.
  - Added the field :code:`invoice_payload` to the class
      :class:`aiogram.types.transaction_partner_user.TransactionPartnerUser`,
      containing the bot-specified invoice payload.
  - Changed the default opening mode for Direct Link Mini Apps.
  - Added support for launching Web Apps via t.me link in the class
      :class:`aiogram.types.menu_button_web_app.MenuButtonWebApp`.
  - Added the field :code:`section_separator_color` to the class :code:`ThemeParams`.
  `#1533 <https://github.com/aiogram/aiogram/issues/1533>`_


Bugfixes
--------

- Fixed event context resolving for the callback query that is coming from the business account
  `#1520 <https://github.com/aiogram/aiogram/issues/1520>`_


3.8.0 (2024-06-19)
===================

Features
--------

- Added utility to safely deserialize any Telegram object or method to a JSON-compatible object (dict).
  (:ref:`>> Read more <serialization-tool>`)
  `#1450 <https://github.com/aiogram/aiogram/issues/1450>`_
- Added full support of `Bot API 7.5 <https://core.telegram.org/bots/api-changelog#june-18-2024>`_

  - Added the classes :class:`aiogram.types.star_transactions.StarTransactions`,
      :class:`aiogram.types.star_transaction.StarTransaction`,
      :class:`aiogram.types.transaction_partner.TransactionPartner`
      and :class:`aiogram.types.revenue_withdrawal_state.RevenueWithdrawalState`,
      containing information about Telegram Star transactions involving the bot.
  - Added the method :class:`aiogram.methods.get_star_transactions.GetStarTransactions`
      that can be used to get the list of all Telegram Star transactions for the bot.
  - Added support for callback buttons in
      :class:`aiogram.types.inline_keyboard_markup.InlineKeyboardMarkup`
      for messages sent on behalf of a business account.
  - Added support for callback queries originating from a message sent
      on behalf of a business account.
  - Added the parameter :code:`business_connection_id` to the methods
      :class:`aiogram.methods.edit_message_text.EditMessageText`,
      :class:`aiogram.methods.edit_message_media.EditMessageMedia`,
      :class:`aiogram.methods.edit_message_caption.EditMessageCaption`,
      :class:`aiogram.methods.edit_message_live_location.EditMessageLiveLocation`,
      :class:`aiogram.methods.stop_message_live_location.StopMessageLiveLocation`
      and :class:`aiogram.methods.edit_message_reply_markup.EditMessageReplyMarkup`,
      allowing the bot to edit business messages.
  - Added the parameter :code:`business_connection_id` to the method
      :class:`aiogram.methods.stop_poll.StopPoll`,
      allowing the bot to stop polls it sent on behalf of a business account.
  `#1518 <https://github.com/aiogram/aiogram/issues/1518>`_


Bugfixes
--------

- Increased DNS cache ttl setting to aiohttp session as a workaround for DNS resolution issues in aiohttp.
  `#1500 <https://github.com/aiogram/aiogram/issues/1500>`_


Improved Documentation
----------------------

- Fixed MongoStorage section in the documentation by adding extra dependency to ReadTheDocs configuration.
  `#1501 <https://github.com/aiogram/aiogram/issues/1501>`_
- Added information about dependency changes to the :code:`2.x --> 3.x` migration guide.
  `#1504 <https://github.com/aiogram/aiogram/issues/1504>`_


Misc
----

- [Only for contributors] Fail redis and mongo tests if incorrect URI provided + some storages tests refactoring

  If incorrect URIs provided to "--redis" and/or "--mongo" options tests should fail with errors instead of skipping.
  Otherwise the next scenario is possible:
    1) developer breaks RedisStorage and/or MongoStorage code
    2) tests are run with incorrect redis and/or mongo URIsprovided by "--redis" and "--mongo" options (for example, wrong port specified)
    3) tests pass because skipping doesn't fail tests run
    4) developer or reviewer doesn't notice that redis and/or mongo tests were skipped
    5) broken code gets in codebase

  Also some refactorings done (related with storages and storages tests).
  `#1510 <https://github.com/aiogram/aiogram/issues/1510>`_


3.7.0 (2024-05-31)
===================

Features
--------

- Added new storage :code:`aiogram.fsm.storage.MongoStorage` for Finite State Machine based on Mongo DB (using :code:`motor` library)
  `#1434 <https://github.com/aiogram/aiogram/issues/1434>`_
- Added full support of `Bot API 7.4 <https://core.telegram.org/bots/api-changelog#may-28-2024>`_
  `#1498 <https://github.com/aiogram/aiogram/issues/1498>`_


Bugfixes
--------

- Fixed wrong :code:`MarkdownV2` custom emoji parsing in :code:`aiogram.utils.text_decorations`
  `#1496 <https://github.com/aiogram/aiogram/issues/1496>`_


Deprecations and Removals
-------------------------

- Removed deprecated arguments from Bot class
  :code:`parse_mode`, :code:`disable_web_page_preview`, :code:`protect_content` as previously announced in v3.4.0.
  `#1494 <https://github.com/aiogram/aiogram/issues/1494>`_


Misc
----

- Improved code consistency and readability in code examples by refactoring imports, adjusting the base webhook URL, modifying bot instance initialization to utilize DefaultBotProperties, and updating router message handlers.
  `#1482 <https://github.com/aiogram/aiogram/issues/1482>`_


3.6.0 (2024-05-06)
===================

Features
--------

- Added full support of `Bot API 7.3 <https://core.telegram.org/bots/api-changelog#may-6-2024>`_
  `#1480 <https://github.com/aiogram/aiogram/issues/1480>`_


Improved Documentation
----------------------

- Added telegram objects transformation block in 2.x -> 3.x migration guide
  `#1412 <https://github.com/aiogram/aiogram/issues/1412>`_


3.5.0 (2024-04-23)
===================

Features
--------

- Added **message_thread_id** parameter to **ChatActionSender** class methods.
  `#1437 <https://github.com/aiogram/aiogram/issues/1437>`_
- Added context manager interface to Bot instance, from now you can use:

  .. code-block:: python

      async with Bot(...) as bot:
          ...

  instead of

  .. code-block:: python

      async with Bot(...).context() as bot:
          ...
  `#1468 <https://github.com/aiogram/aiogram/issues/1468>`_


Bugfixes
--------

- - **WebAppUser Class Fields**: Added missing `is_premium`, `added_to_attachment_menu`, and `allows_write_to_pm` fields to `WebAppUser` class to align with the Telegram API.

  - **WebAppChat Class Implementation**: Introduced the `WebAppChat` class with all its fields (`id`, `type`, `title`, `username`, and `photo_url`) as specified in the Telegram API, which was previously missing from the library.

  - **WebAppInitData Class Fields**: Included previously omitted fields in the `WebAppInitData` class: `chat`, `chat_type`, `chat_instance`, to match the official documentation for a complete Telegram Web Apps support.
  `#1424 <https://github.com/aiogram/aiogram/issues/1424>`_
- Fixed poll answer FSM context by handling :code:`voter_chat` for :code:`poll_answer` event
  `#1436 <https://github.com/aiogram/aiogram/issues/1436>`_
- Added missing error handling to :code:`_background_feed_update` (when in :code:`handle_in_background=True` webhook mode)
  `#1458 <https://github.com/aiogram/aiogram/issues/1458>`_


Improved Documentation
----------------------

- Added WebAppChat class to WebApp docs, updated uk_UA localisation of WebApp docs.
  `#1433 <https://github.com/aiogram/aiogram/issues/1433>`_


Misc
----

- Added full support of `Bot API 7.2 <https://core.telegram.org/bots/api-changelog#march-31-2024>`_
  `#1444 <https://github.com/aiogram/aiogram/issues/1444>`_
- Loosened pydantic version upper restriction from ``<2.7`` to ``<2.8``
  `#1460 <https://github.com/aiogram/aiogram/issues/1460>`_


3.4.1 (2024-02-17)
===================

Bugfixes
--------

- Fixed JSON serialization of the :code:`LinkPreviewOptions` class while it is passed
  as bot-wide default options.
  `#1418 <https://github.com/aiogram/aiogram/issues/1418>`_


3.4.0 (2024-02-16)
===================

Features
--------

- Reworked bot-wide globals like :code:`parse_mode`, :code:`disable_web_page_preview`, and others to be more flexible.

  .. warning::

      Note that the old way of setting these global bot properties is now deprecated and will be removed in the next major release.
  `#1392 <https://github.com/aiogram/aiogram/issues/1392>`_
- A new enum :code:`KeyboardButtonPollTypeType` for :code:`KeyboardButtonPollTypeType.type` field has bed added.
  `#1398 <https://github.com/aiogram/aiogram/issues/1398>`_
- Added full support of `Bot API 7.1 <https://core.telegram.org/bots/api-changelog#february-16-2024>`_

  - Added support for the administrator rights :code:`can_post_stories`, :code:`can_edit_stories`, :code:`can_delete_stories` in supergroups.
  - Added the class :code:`ChatBoostAdded` and the field :code:`boost_added` to the class :code:`Message` for service messages about a user boosting a chat.
  - Added the field :code:`sender_boost_count` to the class :code:`Message`.
  - Added the field :code:`reply_to_story` to the class :code:`Message`.
  - Added the fields :code:`chat` and :code:`id` to the class :code:`Story`.
  - Added the field :code:`unrestrict_boost_count` to the class :code:`Chat`.
  - Added the field :code:`custom_emoji_sticker_set_name` to the class :code:`Chat`.
  `#1417 <https://github.com/aiogram/aiogram/issues/1417>`_


Bugfixes
--------

- Update KeyboardBuilder utility, fixed type-hints for button method, adjusted limits of the different markup types to real world values.
  `#1399 <https://github.com/aiogram/aiogram/issues/1399>`_
- Added new :code:`reply_parameters` param to :code:`message.send_copy` because it hasn't been added there
  `#1403 <https://github.com/aiogram/aiogram/issues/1403>`_


Improved Documentation
----------------------

- Add notion "Working with plural forms" in documentation Utils -> Translation
  `#1395 <https://github.com/aiogram/aiogram/issues/1395>`_


3.3.0 (2023-12-31)
===================

Features
--------

- Added full support of `Bot API 7.0 <https://core.telegram.org/bots/api-changelog#december-29-2023>`_

  - Reactions
  - Replies 2.0
  - Link Preview Customization
  - Block Quotation
  - Multiple Message Actions
  - Requests for multiple users
  - Chat Boosts
  - Giveaway
  - Other changes
  `#1387 <https://github.com/aiogram/aiogram/issues/1387>`_


3.2.0 (2023-11-24)
===================

Features
--------

- Introduced Scenes feature that helps you to simplify user interactions using Finite State Machine.
  Read more about 👉 :ref:`Scenes <Scenes>`.
  `#1280 <https://github.com/aiogram/aiogram/issues/1280>`_
- Added the new FSM strategy :code:`CHAT_TOPIC`, which sets the state for the entire topic in the chat, also works in private messages and regular groups without topics.
  `#1343 <https://github.com/aiogram/aiogram/issues/1343>`_


Bugfixes
--------

- Fixed :code:`parse_mode` argument in the in :code:`Message.send_copy` shortcut. Disable by default.
  `#1332 <https://github.com/aiogram/aiogram/issues/1332>`_
- Added ability to get handler flags from filters.
  `#1360 <https://github.com/aiogram/aiogram/issues/1360>`_
- Fixed a situation where a :code:`CallbackData` could not be parsed without a default value.
  `#1368 <https://github.com/aiogram/aiogram/issues/1368>`_


Improved Documentation
----------------------

- Corrected grammatical errors, improved sentence structures, translation for migration 2.x-3.x
  `#1302 <https://github.com/aiogram/aiogram/issues/1302>`_
- Minor typo correction, specifically in module naming + some grammar.
  `#1340 <https://github.com/aiogram/aiogram/issues/1340>`_
- Added `CITATION.cff` file for automatic academic citation generation.
  Now you can copy citation from the GitHub page and paste it into your paper.
  `#1351 <https://github.com/aiogram/aiogram/issues/1351>`_
- Minor typo correction in middleware docs.
  `#1353 <https://github.com/aiogram/aiogram/issues/1353>`_


Misc
----

- Fixed ResourceWarning in the tests, reworked :code:`RedisEventsIsolation` fixture to use Redis connection from :code:`RedisStorage`
  `#1320 <https://github.com/aiogram/aiogram/issues/1320>`_
- Updated dependencies, bumped minimum required version:

  - :code:`magic-filter` - fixed `.resolve` operation
  - :code:`pydantic` - fixed compatibility (broken in 2.4)
  - :code:`aiodns` - added new dependency to the :code:`fast` extras (:code:`pip install aiogram[fast]`)
  - *others...*
  `#1327 <https://github.com/aiogram/aiogram/issues/1327>`_
- Prevent update handling task pointers from being garbage collected, backport from 2.x
  `#1331 <https://github.com/aiogram/aiogram/issues/1331>`_
- Updated :code:`typing-extensions` package version range in dependencies to fix compatibility with :code:`FastAPI`
  `#1347 <https://github.com/aiogram/aiogram/issues/1347>`_
- Introduce Python 3.12 support
  `#1354 <https://github.com/aiogram/aiogram/issues/1354>`_
- Speeded up CallableMixin processing by caching references to nested objects and simplifying kwargs assembly.
  `#1357 <https://github.com/aiogram/aiogram/issues/1357>`_
- Added :code:`pydantic` v2.5 support.
  `#1361 <https://github.com/aiogram/aiogram/issues/1361>`_
- Updated :code:`thumbnail` fields type to :code:`InputFile` only
  `#1372 <https://github.com/aiogram/aiogram/issues/1372>`_


3.1.1 (2023-09-25)
===================

Bugfixes
--------

- Fixed `pydantic` version <2.4, since 2.4 has breaking changes.
  `#1322 <https://github.com/aiogram/aiogram/issues/1322>`_


3.1.0 (2023-09-22)
===================

Features
--------

- Added support for custom encoders/decoders for payload (and also for deep-linking).
  `#1262 <https://github.com/aiogram/aiogram/issues/1262>`_
- Added :class:`aiogram.utils.input_media.MediaGroupBuilder` for media group construction.
  `#1293 <https://github.com/aiogram/aiogram/issues/1293>`_
- Added full support of `Bot API 6.9 <https://core.telegram.org/bots/api-changelog#september-22-2023>`_
  `#1319 <https://github.com/aiogram/aiogram/issues/1319>`_


Bugfixes
--------

- Added actual param hints for `InlineKeyboardBuilder` and `ReplyKeyboardBuilder`.
  `#1303 <https://github.com/aiogram/aiogram/issues/1303>`_
- Fixed priority of events isolation, now user state will be loaded only after lock is acquired
  `#1317 <https://github.com/aiogram/aiogram/issues/1317>`_


3.0.0 (2023-09-01)
===================

Bugfixes
--------

- Replaced :code:`datetime.datetime` with `DateTime` type wrapper across types to make dumped JSONs object
  more compatible with data that is sent by Telegram.
  `#1277 <https://github.com/aiogram/aiogram/issues/1277>`_
- Fixed magic :code:`.as_(...)` operation for values that can be interpreted as `False` (e.g. `0`).
  `#1281 <https://github.com/aiogram/aiogram/issues/1281>`_
- Italic markdown from utils now uses correct decorators
  `#1282 <https://github.com/aiogram/aiogram/issues/1282>`_
- Fixed method :code:`Message.send_copy` for stickers.
  `#1284 <https://github.com/aiogram/aiogram/issues/1284>`_
- Fixed :code:`Message.send_copy` method, which was not working properly with stories, so not you can copy stories too (forwards messages).
  `#1286 <https://github.com/aiogram/aiogram/issues/1286>`_
- Fixed error overlapping when validation error is caused by remove_unset root validator in base types and methods.
  `#1290 <https://github.com/aiogram/aiogram/issues/1290>`_


3.0.0rc2 (2023-08-18)
======================

Bugfixes
--------

- Fixed missing message content types (:code:`ContentType.USER_SHARED`, :code:`ContentType.CHAT_SHARED`)
  `#1252 <https://github.com/aiogram/aiogram/issues/1252>`_
- Fixed nested hashtag, cashtag and email message entities not being parsed correctly when these entities are inside another entity.
  `#1259 <https://github.com/aiogram/aiogram/issues/1259>`_
- Moved global filters check placement into router to add chance to pass context from global filters
  into handlers in the same way as it possible in other places
  `#1266 <https://github.com/aiogram/aiogram/issues/1266>`_


Improved Documentation
----------------------

- Added error handling example `examples/error_handling.py`
  `#1099 <https://github.com/aiogram/aiogram/issues/1099>`_
- Added a few words about skipping pending updates
  `#1251 <https://github.com/aiogram/aiogram/issues/1251>`_
- Added a section on Dependency Injection technology
  `#1253 <https://github.com/aiogram/aiogram/issues/1253>`_
- This update includes the addition of a multi-file bot example to the repository.
  `#1254 <https://github.com/aiogram/aiogram/issues/1254>`_
- Refactored examples code to use aiogram enumerations and enhanced chat messages with markdown
  beautification's for a more user-friendly display.
  `#1256 <https://github.com/aiogram/aiogram/issues/1256>`_
- Supplemented "Finite State Machine" section in Migration FAQ
  `#1264 <https://github.com/aiogram/aiogram/issues/1264>`_
- Removed extra param in docstring of TelegramEventObserver's filter method
  and fixed typo in I18n documentation.
  `#1268 <https://github.com/aiogram/aiogram/issues/1268>`_


Misc
----

- Enhanced the warning message in dispatcher to include a JSON dump of the update when update type is not known.
  `#1269 <https://github.com/aiogram/aiogram/issues/1269>`_
- Added support for `Bot API 6.8 <https://core.telegram.org/bots/api-changelog#august-18-2023>`_
  `#1275 <https://github.com/aiogram/aiogram/issues/1275>`_


3.0.0rc1 (2023-08-06)
======================

Features
--------

- Added Currency enum.
  You can use it like this:

  .. code-block:: python

      from aiogram.enums import Currency

      await bot.send_invoice(
          ...,
          currency=Currency.USD,
          ...
      )
  `#1194 <https://github.com/aiogram/aiogram/issues/1194>`_
- Updated keyboard builders with new methods for integrating buttons and keyboard creation more seamlessly.
  Added functionality to create buttons from existing markup and attach another builder.
  This improvement aims to make the keyboard building process more user-friendly and flexible.
  `#1236 <https://github.com/aiogram/aiogram/issues/1236>`_
- Added support for message_thread_id in ChatActionSender
  `#1249 <https://github.com/aiogram/aiogram/issues/1249>`_


Bugfixes
--------

- Fixed polling startup when "bot" key is passed manually into dispatcher workflow data
  `#1242 <https://github.com/aiogram/aiogram/issues/1242>`_
- Added codegen configuration for lost shortcuts:

  - ShippingQuery.answer
  - PreCheckoutQuery.answer
  - Message.delete_reply_markup
  `#1244 <https://github.com/aiogram/aiogram/issues/1244>`_


Improved Documentation
----------------------

- Added documentation for webhook and polling modes.
  `#1241 <https://github.com/aiogram/aiogram/issues/1241>`_


Misc
----

- Reworked InputFile reading, removed :code:`__aiter__` method, added `bot: Bot` argument to
  the :code:`.read(...)` method, so, from now URLInputFile can be used without specifying
  bot instance.
  `#1238 <https://github.com/aiogram/aiogram/issues/1238>`_
- Code-generated :code:`__init__` typehints in types and methods to make IDE happy without additional pydantic plugin
  `#1245 <https://github.com/aiogram/aiogram/issues/1245>`_


3.0.0b9 (2023-07-30)
=====================

Features
--------

- Added new shortcuts for :class:`aiogram.types.chat_member_updated.ChatMemberUpdated`
  to send message to chat that member joined/left.
  `#1234 <https://github.com/aiogram/aiogram/issues/1234>`_
- Added new shortcuts for :class:`aiogram.types.chat_join_request.ChatJoinRequest`
  to make easier access to sending messages to users who wants to join to chat.
  `#1235 <https://github.com/aiogram/aiogram/issues/1235>`_


Bugfixes
--------

- Fixed bot assignment in the :code:`Message.send_copy` shortcut
  `#1232 <https://github.com/aiogram/aiogram/issues/1232>`_
- Added model validation to remove UNSET before field validation.
  This change was necessary to correctly handle parse_mode where 'UNSET' is used as a sentinel value.
  Without the removal of 'UNSET', it would create issues when passed to model initialization from Bot.method_name.
  'UNSET' was also added to typing.
  `#1233 <https://github.com/aiogram/aiogram/issues/1233>`_
- Updated pydantic to 2.1 with few bugfixes


Improved Documentation
----------------------

- Improved docs, added basic migration guide (will be expanded later)
  `#1143 <https://github.com/aiogram/aiogram/issues/1143>`_


Deprecations and Removals
-------------------------

- Removed the use of the context instance (Bot.get_current) from all placements that were used previously.
  This is to avoid the use of the context instance in the wrong place.
  `#1230 <https://github.com/aiogram/aiogram/issues/1230>`_


3.0.0b8 (2023-07-17)
=====================

Features
--------

- Added possibility to use custom events in routers (If router does not support custom event it does not break and passes it to included routers).
  `#1147 <https://github.com/aiogram/aiogram/issues/1147>`_
- Added support for FSM in Forum topics.

  The strategy can be changed in dispatcher:

  .. code-block:: python

      from aiogram.fsm.strategy import FSMStrategy
      ...
      dispatcher = Dispatcher(
          fsm_strategy=FSMStrategy.USER_IN_TOPIC,
          storage=...,  # Any persistent storage
      )

  .. note::

      If you have implemented you own storages you should extend record key generation
      with new one attribute - :code:`thread_id`
  `#1161 <https://github.com/aiogram/aiogram/issues/1161>`_
- Improved CallbackData serialization.

  - Minimized UUID (hex without dashes)
  - Replaced bool values with int (true=1, false=0)
  `#1163 <https://github.com/aiogram/aiogram/issues/1163>`_
- Added a tool to make text formatting flexible and easy.
  More details on the :ref:`corresponding documentation page <formatting-tool>`
  `#1172 <https://github.com/aiogram/aiogram/issues/1172>`_
- Added :code:`X-Telegram-Bot-Api-Secret-Token` header check
  `#1173 <https://github.com/aiogram/aiogram/issues/1173>`_
- Made :code:`allowed_updates` list to revolve automatically in start_polling method if not set explicitly.
  `#1178 <https://github.com/aiogram/aiogram/issues/1178>`_
- Added possibility to pass custom headers to :class:`URLInputFile` object
  `#1191 <https://github.com/aiogram/aiogram/issues/1191>`_


Bugfixes
--------

- Change type of result in InlineQueryResult enum for :code:`InlineQueryResultCachedMpeg4Gif`
  and :code:`InlineQueryResultMpeg4Gif` to more correct according to documentation.

  Change regexp for entities parsing to more correct (:code:`InlineQueryResultType.yml`).
  `#1146 <https://github.com/aiogram/aiogram/issues/1146>`_
- Fixed signature of startup/shutdown events to include the :code:`**dispatcher.workflow_data` as the handler arguments.
  `#1155 <https://github.com/aiogram/aiogram/issues/1155>`_
- Added missing :code:`FORUM_TOPIC_EDITED` value to content_type property
  `#1160 <https://github.com/aiogram/aiogram/issues/1160>`_
- Fixed compatibility with Python 3.8-3.9 (from previous release)
  `#1162 <https://github.com/aiogram/aiogram/issues/1162>`_
- Fixed the markdown spoiler parser.
  `#1176 <https://github.com/aiogram/aiogram/issues/1176>`_
- Fixed workflow data propagation
  `#1196 <https://github.com/aiogram/aiogram/issues/1196>`_
- Fixed the serialization error associated with nested subtypes
  like InputMedia, ChatMember, etc.

  The previously generated code resulted in an invalid schema under pydantic v2,
  which has stricter type parsing.
  Hence, subtypes without the specification of all subtype unions were generating
  an empty object. This has been rectified now.
  `#1213 <https://github.com/aiogram/aiogram/issues/1213>`_


Improved Documentation
----------------------

- Changed small grammar typos for :code:`upload_file`
  `#1133 <https://github.com/aiogram/aiogram/issues/1133>`_


Deprecations and Removals
-------------------------

- Removed text filter in due to is planned to remove this filter few versions ago.

  Use :code:`F.text` instead
  `#1170 <https://github.com/aiogram/aiogram/issues/1170>`_


Misc
----

- Added full support of `Bot API 6.6 <https://core.telegram.org/bots/api-changelog#march-9-2023>`_

  .. danger::

      Note that this issue has breaking changes described in the Bot API changelog,
      this changes is not breaking in the API but breaking inside aiogram because
      Beta stage is not finished.
  `#1139 <https://github.com/aiogram/aiogram/issues/1139>`_
- Added full support of `Bot API 6.7 <https://core.telegram.org/bots/api-changelog#april-21-2023>`_

  .. warning::

      Note that arguments *switch_pm_parameter* and *switch_pm_text* was deprecated
      and should be changed to *button* argument as described in API docs.
  `#1168 <https://github.com/aiogram/aiogram/issues/1168>`_
- Updated `Pydantic to V2 <https://docs.pydantic.dev/2.0/migration/>`_

  .. warning::

      Be careful, not all libraries is already updated to using V2
  `#1202 <https://github.com/aiogram/aiogram/issues/1202>`_
- Added global defaults :code:`disable_web_page_preview` and :code:`protect_content` in addition to :code:`parse_mode` to the Bot instance,
  reworked internal request builder mechanism.
  `#1142 <https://github.com/aiogram/aiogram/issues/1142>`_
- Removed bot parameters from storages
  `#1144 <https://github.com/aiogram/aiogram/issues/1144>`_

- Replaced ContextVar's with a new feature called `Validation Context <https://docs.pydantic.dev/latest/usage/validators/#validation-context>`_
  in Pydantic to improve the clarity, usability, and versatility of handling the Bot instance within method shortcuts.

  .. danger::

    **Breaking**: The 'bot' argument now is required in `URLInputFile`
  `#1210 <https://github.com/aiogram/aiogram/issues/1210>`_
- Updated magic-filter with new features

  - Added hint for :code:`len(F)` error
  - Added not in operation
  `#1221 <https://github.com/aiogram/aiogram/issues/1221>`_


3.0.0b7 (2023-02-18)
=====================

.. warning::

    Note that this version has incompatibility with Python 3.8-3.9 in case when you create an instance of Dispatcher outside of the any coroutine.

    Sorry for the inconvenience, it will be fixed in the next version.

    This code will not work:

    .. code-block:: python

        dp = Dispatcher()

        def main():
            ...
            dp.run_polling(...)

        main()

    But if you change it like this it should works as well:

    .. code-block:: python

        router = Router()

        async def main():
            dp = Dispatcher()
            dp.include_router(router)
            ...
            dp.start_polling(...)

        asyncio.run(main())


Features
--------

- Added missing shortcuts, new enums, reworked old stuff

  **Breaking**
  All previously added enums is re-generated in new place - `aiogram.enums` instead of `aiogram.types`

  **Added enums:** :class:`aiogram.enums.bot_command_scope_type.BotCommandScopeType`,
      :class:`aiogram.enums.chat_action.ChatAction`,
      :class:`aiogram.enums.chat_member_status.ChatMemberStatus`,
      :class:`aiogram.enums.chat_type.ChatType`,
      :class:`aiogram.enums.content_type.ContentType`,
      :class:`aiogram.enums.dice_emoji.DiceEmoji`,
      :class:`aiogram.enums.inline_query_result_type.InlineQueryResultType`,
      :class:`aiogram.enums.input_media_type.InputMediaType`,
      :class:`aiogram.enums.mask_position_point.MaskPositionPoint`,
      :class:`aiogram.enums.menu_button_type.MenuButtonType`,
      :class:`aiogram.enums.message_entity_type.MessageEntityType`,
      :class:`aiogram.enums.parse_mode.ParseMode`,
      :class:`aiogram.enums.poll_type.PollType`,
      :class:`aiogram.enums.sticker_type.StickerType`,
      :class:`aiogram.enums.topic_icon_color.TopicIconColor`,
      :class:`aiogram.enums.update_type.UpdateType`,

  **Added shortcuts**:

  - *Chat* :meth:`aiogram.types.chat.Chat.get_administrators`,
      :meth:`aiogram.types.chat.Chat.delete_message`,
      :meth:`aiogram.types.chat.Chat.revoke_invite_link`,
      :meth:`aiogram.types.chat.Chat.edit_invite_link`,
      :meth:`aiogram.types.chat.Chat.create_invite_link`,
      :meth:`aiogram.types.chat.Chat.export_invite_link`,
      :meth:`aiogram.types.chat.Chat.do`,
      :meth:`aiogram.types.chat.Chat.delete_sticker_set`,
      :meth:`aiogram.types.chat.Chat.set_sticker_set`,
      :meth:`aiogram.types.chat.Chat.get_member`,
      :meth:`aiogram.types.chat.Chat.get_member_count`,
      :meth:`aiogram.types.chat.Chat.leave`,
      :meth:`aiogram.types.chat.Chat.unpin_all_messages`,
      :meth:`aiogram.types.chat.Chat.unpin_message`,
      :meth:`aiogram.types.chat.Chat.pin_message`,
      :meth:`aiogram.types.chat.Chat.set_administrator_custom_title`,
      :meth:`aiogram.types.chat.Chat.set_permissions`,
      :meth:`aiogram.types.chat.Chat.promote`,
      :meth:`aiogram.types.chat.Chat.restrict`,
      :meth:`aiogram.types.chat.Chat.unban`,
      :meth:`aiogram.types.chat.Chat.ban`,
      :meth:`aiogram.types.chat.Chat.set_description`,
      :meth:`aiogram.types.chat.Chat.set_title`,
      :meth:`aiogram.types.chat.Chat.delete_photo`,
      :meth:`aiogram.types.chat.Chat.set_photo`,
  - *Sticker*: :meth:`aiogram.types.sticker.Sticker.set_position_in_set`,
      :meth:`aiogram.types.sticker.Sticker.delete_from_set`,
  - *User*: :meth:`aiogram.types.user.User.get_profile_photos`
  `#952 <https://github.com/aiogram/aiogram/issues/952>`_
- Added :ref:`callback answer <callback-answer-util>` feature
  `#1091 <https://github.com/aiogram/aiogram/issues/1091>`_
- Added a method that allows you to compactly register routers
  `#1117 <https://github.com/aiogram/aiogram/issues/1117>`_


Bugfixes
--------

- Check status code when downloading file
  `#816 <https://github.com/aiogram/aiogram/issues/816>`_
- Fixed `ignore_case` parameter in :obj:`aiogram.filters.command.Command` filter
  `#1106 <https://github.com/aiogram/aiogram/issues/1106>`_


Misc
----

- Added integration with new code-generator named `Butcher <https://github.com/aiogram/butcher>`_
  `#1069 <https://github.com/aiogram/aiogram/issues/1069>`_
- Added full support of `Bot API 6.4 <https://core.telegram.org/bots/api-changelog#december-30-2022>`_
  `#1088 <https://github.com/aiogram/aiogram/issues/1088>`_
- Updated package metadata, moved build internals from Poetry to Hatch, added contributing guides.
  `#1095 <https://github.com/aiogram/aiogram/issues/1095>`_
- Added full support of `Bot API 6.5 <https://core.telegram.org/bots/api-changelog#february-3-2023>`_

  .. danger::

      Note that :obj:`aiogram.types.chat_permissions.ChatPermissions` is updated without
      backward compatibility, so now this object has no :code:`can_send_media_messages` attribute
  `#1112 <https://github.com/aiogram/aiogram/issues/1112>`_
- Replaced error :code:`TypeError: TelegramEventObserver.__call__() got an unexpected keyword argument '<name>'`
  with a more understandable one for developers and with a link to the documentation.
  `#1114 <https://github.com/aiogram/aiogram/issues/1114>`_
- Added possibility to reply into webhook with files
  `#1120 <https://github.com/aiogram/aiogram/issues/1120>`_
- Reworked graceful shutdown. Added method to stop polling.
  Now polling started from dispatcher can be stopped by signals gracefully without errors (on Linux and Mac).
  `#1124 <https://github.com/aiogram/aiogram/issues/1124>`_


3.0.0b6 (2022-11-18)
=====================

Features
--------

- (again) Added possibility to combine filters with an *and*/*or* operations.

  Read more in ":ref:`Combining filters <combining-filters>`" documentation section
  `#1018 <https://github.com/aiogram/aiogram/issues/1018>`_
- Added following methods to ``Message`` class:

  - :code:`Message.forward(...)`
  - :code:`Message.edit_media(...)`
  - :code:`Message.edit_live_location(...)`
  - :code:`Message.stop_live_location(...)`
  - :code:`Message.pin(...)`
  - :code:`Message.unpin()`
  `#1030 <https://github.com/aiogram/aiogram/issues/1030>`_
- Added following methods to :code:`User` class:

  - :code:`User.mention_markdown(...)`
  - :code:`User.mention_html(...)`
  `#1049 <https://github.com/aiogram/aiogram/issues/1049>`_
- Added full support of `Bot API 6.3 <https://core.telegram.org/bots/api-changelog#november-5-2022>`_
  `#1057 <https://github.com/aiogram/aiogram/issues/1057>`_


Bugfixes
--------

- Fixed :code:`Message.send_invoice` and :code:`Message.reply_invoice`, added missing arguments
  `#1047 <https://github.com/aiogram/aiogram/issues/1047>`_
- Fixed copy and forward in:

  - :code:`Message.answer(...)`
  - :code:`Message.copy_to(...)`
  `#1064 <https://github.com/aiogram/aiogram/issues/1064>`_


Improved Documentation
----------------------

- Fixed UA translations in index.po
  `#1017 <https://github.com/aiogram/aiogram/issues/1017>`_
- Fix typehints for :code:`Message`, :code:`reply_media_group` and :code:`answer_media_group` methods
  `#1029 <https://github.com/aiogram/aiogram/issues/1029>`_
- Removed an old now non-working feature
  `#1060 <https://github.com/aiogram/aiogram/issues/1060>`_


Misc
----

- Enabled testing on Python 3.11
  `#1044 <https://github.com/aiogram/aiogram/issues/1044>`_
- Added a mandatory dependency :code:`certifi` in due to in some cases on systems that doesn't have updated ca-certificates the requests to Bot API fails with reason :code:`[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self signed certificate in certificate chain`
  `#1066 <https://github.com/aiogram/aiogram/issues/1066>`_


3.0.0b5 (2022-10-02)
=====================

Features
--------

- Add PyPy support and run tests under PyPy
  `#985 <https://github.com/aiogram/aiogram/issues/985>`_
- Added message text to aiogram exceptions representation
  `#988 <https://github.com/aiogram/aiogram/issues/988>`_
- Added warning about using magic filter from `magic_filter` instead of `aiogram`'s ones.
  Is recommended to use `from aiogram import F` instead of `from magic_filter import F`
  `#990 <https://github.com/aiogram/aiogram/issues/990>`_
- Added more detailed error when server response can't be deserialized. This feature will help to debug unexpected responses from the Server
  `#1014 <https://github.com/aiogram/aiogram/issues/1014>`_


Bugfixes
--------

- Reworked error event, introduced :class:`aiogram.types.error_event.ErrorEvent` object.
  `#898 <https://github.com/aiogram/aiogram/issues/898>`_
- Fixed escaping markdown in `aiogram.utils.markdown` module
  `#903 <https://github.com/aiogram/aiogram/issues/903>`_
- Fixed polling crash when Telegram Bot API raises HTTP 429 status-code.
  `#995 <https://github.com/aiogram/aiogram/issues/995>`_
- Fixed empty mention in command parsing, now it will be None instead of an empty string
  `#1013 <https://github.com/aiogram/aiogram/issues/1013>`_


Improved Documentation
----------------------

- Initialized Docs translation (added Ukrainian language)
  `#925 <https://github.com/aiogram/aiogram/issues/925>`_


Deprecations and Removals
-------------------------

- Removed filters factory as described in corresponding issue.
  `#942 <https://github.com/aiogram/aiogram/issues/942>`_


Misc
----

- Now Router/Dispatcher accepts only keyword arguments.
  `#982 <https://github.com/aiogram/aiogram/issues/982>`_


3.0.0b4 (2022-08-14)
=====================

Features
--------

- Add class helper ChatAction for constants that Telegram BotAPI uses in sendChatAction request.
  In my opinion, this will help users and will also improve compatibility with 2.x version
  where similar class was called "ChatActions".
  `#803 <https://github.com/aiogram/aiogram/issues/803>`_
- Added possibility to combine filters or invert result

  Example:

  .. code-block:: python

      Text(text="demo") | Command(commands=["demo"])
      MyFilter() & AnotherFilter()
      ~StateFilter(state='my-state')

  `#894 <https://github.com/aiogram/aiogram/issues/894>`_
- Fixed type hints for redis TTL params.
  `#922 <https://github.com/aiogram/aiogram/issues/922>`_
- Added `full_name` shortcut for `Chat` object
  `#929 <https://github.com/aiogram/aiogram/issues/929>`_


Bugfixes
--------

- Fixed false-positive coercing of Union types in API methods
  `#901 <https://github.com/aiogram/aiogram/issues/901>`_
- Added 3 missing content types:

  * proximity_alert_triggered
  * supergroup_chat_created
  * channel_chat_created
  `#906 <https://github.com/aiogram/aiogram/issues/906>`_
- Fixed the ability to compare the state, now comparison to copy of the state will return `True`.
  `#927 <https://github.com/aiogram/aiogram/issues/927>`_
- Fixed default lock kwargs in RedisEventIsolation.
  `#972 <https://github.com/aiogram/aiogram/issues/972>`_


Misc
----

- Restrict including routers with strings
  `#896 <https://github.com/aiogram/aiogram/issues/896>`_
- Changed CommandPatterType to CommandPatternType in `aiogram/dispatcher/filters/command.py`
  `#907 <https://github.com/aiogram/aiogram/issues/907>`_
- Added full support of `Bot API 6.1 <https://core.telegram.org/bots/api-changelog#june-20-2022>`_
  `#936 <https://github.com/aiogram/aiogram/issues/936>`_
- **Breaking!** More flat project structure

  These packages was moved, imports in your code should be fixed:

  - :code:`aiogram.dispatcher.filters` -> :code:`aiogram.filters`
  - :code:`aiogram.dispatcher.fsm` -> :code:`aiogram.fsm`
  - :code:`aiogram.dispatcher.handler` -> :code:`aiogram.handler`
  - :code:`aiogram.dispatcher.webhook` -> :code:`aiogram.webhook`
  - :code:`aiogram.dispatcher.flags/*` -> :code:`aiogram.dispatcher.flags` (single module instead of package)
  `#938 <https://github.com/aiogram/aiogram/issues/938>`_
- Removed deprecated :code:`router.<event>_handler` and :code:`router.register_<event>_handler` methods.
  `#941 <https://github.com/aiogram/aiogram/issues/941>`_
- Deprecated filters factory. It will be removed in next Beta (3.0b5)
  `#942 <https://github.com/aiogram/aiogram/issues/942>`_
- `MessageEntity` method `get_text` was removed and `extract` was renamed to `extract_from`
  `#944 <https://github.com/aiogram/aiogram/issues/944>`_
- Added full support of `Bot API 6.2 <https://core.telegram.org/bots/api-changelog#august-12-2022>`_
  `#975 <https://github.com/aiogram/aiogram/issues/975>`_


3.0.0b3 (2022-04-19)
=====================

Features
--------

- Added possibility to get command magic result as handler argument
  `#889 <https://github.com/aiogram/aiogram/issues/889>`_
- Added full support of `Telegram Bot API 6.0 <https://core.telegram.org/bots/api-changelog#april-16-2022>`_
  `#890 <https://github.com/aiogram/aiogram/issues/890>`_


Bugfixes
--------

- Fixed I18n lazy-proxy. Disabled caching.
  `#839 <https://github.com/aiogram/aiogram/issues/839>`_
- Added parsing of spoiler message entity
  `#865 <https://github.com/aiogram/aiogram/issues/865>`_
- Fixed default `parse_mode` for `Message.copy_to()` method.
  `#876 <https://github.com/aiogram/aiogram/issues/876>`_
- Fixed CallbackData factory parsing IntEnum's
  `#885 <https://github.com/aiogram/aiogram/issues/885>`_


Misc
----

- Added automated check that pull-request adds a changes description to **CHANGES** directory
  `#873 <https://github.com/aiogram/aiogram/issues/873>`_
- Changed :code:`Message.html_text` and :code:`Message.md_text` attributes behaviour when message has no text.
  The empty string will be used instead of raising error.
  `#874 <https://github.com/aiogram/aiogram/issues/874>`_
- Used `redis-py` instead of `aioredis` package in due to this packages was merged into single one
  `#882 <https://github.com/aiogram/aiogram/issues/882>`_
- Solved common naming problem with middlewares that confusing too much developers
  - now you can't see the `middleware` and `middlewares` attributes at the same point
  because this functionality encapsulated to special interface.
  `#883 <https://github.com/aiogram/aiogram/issues/883>`_


3.0.0b2 (2022-02-19)
=====================

Features
--------

- Added possibility to pass additional arguments into the aiohttp webhook handler to use this
  arguments inside handlers as the same as it possible in polling mode.
  `#785 <https://github.com/aiogram/aiogram/issues/785>`_
- Added possibility to add handler flags via decorator (like `pytest.mark` decorator but `aiogram.flags`)
  `#836 <https://github.com/aiogram/aiogram/issues/836>`_
- Added :code:`ChatActionSender` utility to automatically sends chat action while long process is running.

  It also can be used as message middleware and can be customized via :code:`chat_action` flag.
  `#837 <https://github.com/aiogram/aiogram/issues/837>`_


Bugfixes
--------

- Fixed unexpected behavior of sequences in the StateFilter.
  `#791 <https://github.com/aiogram/aiogram/issues/791>`_
- Fixed exceptions filters
  `#827 <https://github.com/aiogram/aiogram/issues/827>`_


Misc
----

- Logger name for processing events is changed to :code:`aiogram.events`.
  `#830 <https://github.com/aiogram/aiogram/issues/830>`_
- Added full support of Telegram Bot API 5.6 and 5.7
  `#835 <https://github.com/aiogram/aiogram/issues/835>`_
- **BREAKING**
  Events isolation mechanism is moved from FSM storages to standalone managers
  `#838 <https://github.com/aiogram/aiogram/issues/838>`_


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
