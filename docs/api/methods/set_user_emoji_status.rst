##################
setUserEmojiStatus
##################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.set_user_emoji_status
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.set_user_emoji_status(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.set_user_emoji_status import SetUserEmojiStatus`
- alias: :code:`from aiogram.methods import SetUserEmojiStatus`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(SetUserEmojiStatus(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SetUserEmojiStatus(...)
