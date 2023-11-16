.. _Keyboard builder:

================
Keyboard builder
================

Keyboard builder helps to dynamically generate markup.

.. note::

    Note that if you have static markup, it's best to define it explicitly rather than using builder,
    but if you have dynamic markup configuration, feel free to use builder as you wish.


Usage example
=============

For example you want to generate inline keyboard with 10 buttons

.. code-block:: python

    builder = InlineKeyboardBuilder()

    for index in range(1, 11):
        builder.button(text=f"Set {index}", callback_data=f"set:{index}")


then adjust this buttons to some grid, for example first line will have 3 buttons, the next lines will have 2 buttons

.. code-block::

    builder.adjust(3, 2)

also you can attach another builder to this one

.. code-block:: python

    another_builder = InlineKeyboardBuilder(...)...  # Another builder with some buttons
    builder.attach(another_builder)

or you can attach some already generated markup

.. code-block:: python

    markup = InlineKeyboardMarkup(inline_keyboard=[...])  # Some markup
    builder.attach(InlineKeyboardBuilder.from_markup(markup))

and finally you can export this markup to use it in your message

.. code-block:: python

    await message.answer("Some text here", reply_markup=builder.as_markup())

Reply keyboard builder has the same interface

.. warning::

    Note that you can't attach reply keyboard builder to inline keyboard builder and vice versa


Inline Keyboard
===============

.. autoclass:: aiogram.utils.keyboard.InlineKeyboardBuilder
    :members: __init__, buttons, copy, export, add, row, adjust, from_markup, attach

    .. method:: button(text: str, url: Optional[str] = None, login_url: Optional[LoginUrl] = None, callback_data: Optional[Union[str, CallbackData]] = None, switch_inline_query: Optional[str] = None, switch_inline_query_current_chat: Optional[str] = None, callback_game: Optional[CallbackGame] = None, pay: Optional[bool] = None, **kwargs: Any) -> aiogram.utils.keyboard.InlineKeyboardBuilder
        :noindex:

        Add new inline button to markup

    .. method:: as_markup() -> aiogram.types.inline_keyboard_markup.InlineKeyboardMarkup
        :noindex:

        Construct an InlineKeyboardMarkup

Reply Keyboard
==============

.. autoclass:: aiogram.utils.keyboard.ReplyKeyboardBuilder
    :members: __init__, buttons, copy, export, add, row, adjust, from_markup, attach

    .. method:: button(text: str, request_contact: Optional[bool] = None, request_location: Optional[bool] = None, request_poll: Optional[KeyboardButtonPollType] = None, **kwargs: Any) -> aiogram.utils.keyboard.ReplyKeyboardBuilder
        :noindex:

        Add new button to markup

    .. method:: as_markup() -> aiogram.types.reply_keyboard_markup.ReplyKeyboardMarkup
        :noindex:

        Construct an ReplyKeyboardMarkup
