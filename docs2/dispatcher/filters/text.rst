====
Text
====

.. autoclass:: aiogram.dispatcher.filters.text.Text
    :members:
    :member-order: bysource
    :undoc-members: False

Can be imported:

- :code:`from aiogram.dispatcher.filters.text import Text`
- :code:`from aiogram.dispatcher.filters import Text`
- :code:`from aiogram.filters import Text`

Or used from filters factory by passing corresponding arguments to handler registration line

Usage
=====

#. Text equals with the specified value: :code:`Text(text="text")  # value == 'text'`
#. Text starts with the specified value: :code:`Text(text_startswith="text")  # value.startswith('text')`
#. Text ends with the specified value: :code:`Text(text_endswith="text")  # value.endswith('text')`
#. Text contains the specified value: :code:`Text(text_contains="text")  # value in 'text'`
#. Any of previous listed filters can be list, set or tuple of strings that's mean any of listed value should be equals/startswith/endswith/contains: :code:`Text(text=["text", "spam"])`
#. Ignore case can be combined with any previous listed filter: :code:`Text(text="Text", text_ignore_case=True)  # value.lower() == 'text'.lower()`

Allowed handlers
================

Allowed update types for this filter:

- :code:`message`
- :code:`edited_message`
- :code:`channel_post`
- :code:`edited_channel_post`
- :code:`inline_query`
- :code:`callback_query`
