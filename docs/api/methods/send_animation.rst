#############
sendAnimation
#############

Returns: :obj:`Message`

.. automodule:: aiogram.methods.send_animation
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: Message = await bot.send_animation(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.send_animation import SendAnimation`
- alias: :code:`from aiogram.methods import SendAnimation`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Message = await bot(SendAnimation(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SendAnimation(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.message.Message.answer_animation`
- :meth:`aiogram.types.message.Message.reply_animation`
- :meth:`aiogram.types.chat_join_request.ChatJoinRequest.answer_animation`
- :meth:`aiogram.types.chat_join_request.ChatJoinRequest.answer_animation_pm`
- :meth:`aiogram.types.chat_member_updated.ChatMemberUpdated.answer_animation`
