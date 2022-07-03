##################
restrictChatMember
##################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.restrict_chat_member
    :members:
    :member-order: bysource
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.restrict_chat_member(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.restrict_chat_member import RestrictChatMember`
- alias: :code:`from aiogram.methods import RestrictChatMember`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(RestrictChatMember(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return RestrictChatMember(...)
