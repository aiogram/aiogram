=========
MagicData
=========

Usage
=====

#. :code:`MagicData(F.event.from_user.id == F.config.admin_id)`  (Note that :code:`config` should be passed from middleware)

Explanation
===========

.. autoclass:: aiogram.filters.magic_data.MagicData
    :members:
    :member-order: bysource
    :undoc-members: False

Can be imported:

- :code:`from aiogram.filters import MagicData`


Allowed handlers
================

Allowed update types for this filter:

- :code:`message`
- :code:`edited_message`
- :code:`channel_post`
- :code:`edited_channel_post`
- :code:`inline_query`
- :code:`chosen_inline_result`
- :code:`callback_query`
- :code:`shipping_query`
- :code:`pre_checkout_query`
- :code:`poll`
- :code:`poll_answer`
- :code:`my_chat_member`
- :code:`chat_member`
- :code:`chat_join_request`
- :code:`error`
