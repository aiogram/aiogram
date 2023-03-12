.. _keyboard-builder
================
Keyboard builder
================

Keyboard builder helps to dynamically generate markup.

.. note::

    Note that if you have static markup, it's best to define it explicitly rather than using builder,
    but if you have dynamic markup configuration, feel free to use builder as you wish.


Usage example
=============

.. code-block:: python

    builder = InlineKeyboardBuilder()

    for index in range(1, 11):
        builder.button(text=f"Set {index}", callback_data=f"set:{index}")

    builder.adjust(3, 2)

    await message.answer("Some text here", reply_markup=builder.as_markup())


Base builder
============
.. autoclass:: aiogram.utils.keyboard.ReplyKeyboardBuilder
    :members: __init__, buttons, copy, export, add, row, adjust, button, as_markup
    :undoc-members: True

Inline Keyboard
===============

.. autoclass:: aiogram.utils.keyboard.InlineKeyboardBuilder
    :noindex:

    .. method:: button(text: str, url: Optional[str] = None, login_url: Optional[LoginUrl] = None, callback_data: Optional[Union[str, CallbackData]] = None, switch_inline_query: Optional[str] = None, switch_inline_query_current_chat: Optional[str] = None, callback_game: Optional[CallbackGame] = None, pay: Optional[bool] = None, **kwargs: Any) -> aiogram.utils.keyboard.InlineKeyboardBuilder
        :noindex:

        Add new inline button to markup

    .. method:: as_markup() -> aiogram.types.inline_keyboard_markup.InlineKeyboardMarkup
        :noindex:

        Construct an InlineKeyboardMarkup

Reply Keyboard
==============

.. autoclass:: aiogram.utils.keyboard.ReplyKeyboardBuilder
    :noindex:

    .. method:: button(text: str, request_contact: Optional[bool] = None, request_location: Optional[bool] = None, request_poll: Optional[KeyboardButtonPollType] = None, **kwargs: Any) -> aiogram.utils.keyboard.ReplyKeyboardBuilder
        :noindex:

        Add new button to markup

    .. method:: as_markup() -> aiogram.types.reply_keyboard_markup.ReplyKeyboardMarkup
        :noindex:

        Construct an ReplyKeyboardMarkup
