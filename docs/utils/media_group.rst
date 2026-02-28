===================
Media group
===================

This module provides tools for media groups.

Building media groups
=====================

Media group builder can be used to build media groups
for :class:`aiogram.types.input_media_photo.InputMediaPhoto`, :class:`aiogram.types.input_media_video.InputMediaVideo`,
:class:`aiogram.types.input_media_document.InputMediaDocument` and :class:`aiogram.types.input_media_audio.InputMediaAudio`.

.. warning::

    :class:`aiogram.types.input_media_animation.InputMediaAnimation`
    is not supported yet in the Bot API to send as media group.


Usage
=====

.. code-block:: python

    media_group = MediaGroupBuilder(caption="Media group caption")

    # Add photo
    media_group.add_photo(media="https://picsum.photos/200/300")
    # Dynamically add photo with known type without using separate method
    media_group.add(type="photo", media="https://picsum.photos/200/300")
    # ... or video
    media_group.add(type="video", media=FSInputFile("media/video.mp4"))


To send media group use :meth:`aiogram.methods.send_media_group.SendMediaGroup` method,
but when you use :class:`aiogram.utils.media_group.MediaGroupBuilder`
you should pass ``media`` argument as ``media_group.build()``.

If you specify ``caption`` in :class:`aiogram.utils.media_group.MediaGroupBuilder`
it will be used as ``caption`` for first media in group.

.. code-block:: python

    await bot.send_media_group(chat_id=chat_id, media=media_group.build())


Handling media groups
======================

By default each media in the group is processed separately.

You can use :class:`aiogram.dispatcher.middlewares.media_group.MediaGroupAggregatorMiddleware`
to process media groups as one. If you do, only one message from the group will be processed, and updates for
other messages with the same media group ID will be suppressed.

You also can use :class:`aiogram.filters.media_group.MediaGroupFilter`
to filter media groups.

Usage
=====

.. code-block:: python

    from aiogram import F
    from aiogram.types import Message

    # register middleware
    from aiogram.dispatcher.middlewares.media_group import MediaGroupAggregatorMiddleware
    from aiogram.filters.media_group import MediaGroupFilter

    router.message.outer_middleware(MediaGroupAggregatorMiddleware())

    # use middleware
    @router.message(
      MediaGroupFilter(max_count=5),
      F.caption == "album_caption" # other filters will be applied to the first message in the group
    )
    async def start(message: Message, album: list[Message]):
      # message is the first media in this group
      # album is list of all messages with the same mediaGroupId, including current message
      await message.answer(
        f"You sent {len(album)} media in the group. "
        f"Media group ID: {message.media_group_id}. "
        f"Album messages: {', '.join(str(m.message_id) for m in album)}"
      )

References
==========

.. autoclass:: aiogram.utils.media_group.MediaGroupBuilder
   :members:
.. autoclass:: aiogram.dispatcher.middlewares.media_group.MediaGroupAggregatorMiddleware
   :members:
.. autoclass:: aiogram.filters.media_group.MediaGroupFilter
   :members:
