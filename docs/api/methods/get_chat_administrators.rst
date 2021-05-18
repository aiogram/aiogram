#####################
getChatAdministrators
#####################

Returns: :obj:`List[ChatMember]`

.. automodule:: aiogram.methods.get_chat_administrators
    :members:
    :member-order: bysource
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: List[ChatMember] = await bot.get_chat_administrators(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.get_chat_administrators import GetChatAdministrators`
- alias: :code:`from aiogram.methods import GetChatAdministrators`

In handlers with current bot
----------------------------

.. code-block:: python

    result: List[ChatMember] = await GetChatAdministrators(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: List[ChatMember] = await bot(GetChatAdministrators(...))
