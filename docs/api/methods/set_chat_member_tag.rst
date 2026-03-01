################
setChatMemberTag
################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.set_chat_member_tag
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.set_chat_member_tag(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.set_chat_member_tag import SetChatMemberTag`
- alias: :code:`from aiogram.methods import SetChatMemberTag`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(SetChatMemberTag(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SetChatMemberTag(...)
