====
MagicData
====

.. autoclass:: aiogram.dispatcher.filters.magic_data.MagicData
    :members:
    :member-order: bysource
    :undoc-members: False

Can be imported:

- :code:`from aiogram.dispatcher.filters.magic_data import MagicData`
- :code:`from aiogram.dispatcher.filters import MagicData`
- :code:`from aiogram.filters import MagicData`

Or used from filters factory by passing corresponding arguments to handler registration line

Usage
=====

#. :code:`magic_data=F.event.from_user.id == F.config.admin_id`  (Note that :code:`config` should be passed from middleware)


Allowed handlers
================

Allowed update types for this filter:

- :code:`message`
- :code:`edited_message`
- :code:`channel_post`
- :code:`edited_channel_post`
- :code:`inline_query`
- :code:`callback_query`
