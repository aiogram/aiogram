###########################
getUserPersonalChatMessages
###########################

Returns: :obj:`list[Message]`

.. automodule:: aiogram.methods.get_user_personal_chat_messages
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: list[Message] = await bot.get_user_personal_chat_messages(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.get_user_personal_chat_messages import GetUserPersonalChatMessages`
- alias: :code:`from aiogram.methods import GetUserPersonalChatMessages`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: list[Message] = await bot(GetUserPersonalChatMessages(...))
