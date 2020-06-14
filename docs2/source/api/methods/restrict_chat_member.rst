##################
restrictChatMember
##################

Use this method to restrict a user in a supergroup. The bot must be an administrator in the supergroup for this to work and must have the appropriate admin rights. Pass True for all permissions to lift restrictions from a user. Returns True on success.

Returns: :obj:`bool`

.. automodule:: aiogram.api.methods.restrict_chat_member
    :members:


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.restrict_chat_member(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import RestrictChatMember`
- :code:`from aiogram.api.methods import RestrictChatMember`
- :code:`from aiogram.api.methods.restrict_chat_member import RestrictChatMember`

In handlers with current bot
----------------------------

.. code-block::

    result: bool = await RestrictChatMember(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: bool = await bot(RestrictChatMember(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return RestrictChatMember(...)