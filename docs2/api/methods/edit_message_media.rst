################
editMessageMedia
################

Use this method to edit animation, audio, document, photo, or video messages. If a message is a part of a message album, then it can be edited only to a photo or a video. Otherwise, message type can be changed arbitrarily. When inline message is edited, new file can't be uploaded. Use previously uploaded file via its file_id or specify a URL. On success, if the edited message was sent by the bot, the edited Message is returned, otherwise True is returned.

Returns: :obj:`Union[Message, bool]`

.. automodule:: aiogram.methods.edit_message_media
    :members:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: Union[Message, bool] = await bot.edit_message_media(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import EditMessageMedia`
- :code:`from aiogram.methods import EditMessageMedia`
- :code:`from aiogram.methods.edit_message_media import EditMessageMedia`

In handlers with current bot
----------------------------

.. code-block::

    result: Union[Message, bool] = await EditMessageMedia(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: Union[Message, bool] = await bot(EditMessageMedia(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return EditMessageMedia(...)