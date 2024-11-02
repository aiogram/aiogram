#########################
getForumTopicIconStickers
#########################

Returns: :obj:`list[Sticker]`

.. automodule:: aiogram.methods.get_forum_topic_icon_stickers
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: list[Sticker] = await bot.get_forum_topic_icon_stickers(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.get_forum_topic_icon_stickers import GetForumTopicIconStickers`
- alias: :code:`from aiogram.methods import GetForumTopicIconStickers`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: list[Sticker] = await bot(GetForumTopicIconStickers(...))
