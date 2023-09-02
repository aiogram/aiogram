===================
Media group builder
===================

This module provides a builder for media groups, it can be used to build media groups
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


References
==========

.. autoclass:: aiogram.utils.media_group.MediaGroupBuilder
   :members:
