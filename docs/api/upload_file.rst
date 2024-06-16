.. _sending-files:

###################
How to upload file?
###################

As says `official Telegram Bot API documentation <https://core.telegram.org/bots/api#sending-files>`_
there are three ways to send files (photos, stickers, audio, media, etc.):

If the file is already stored somewhere on the Telegram servers or file is available by the URL,
you don't need to reupload it.

But if you need to upload a new file just use subclasses of `InputFile <types/input_file.html>`__.

Here are the three different available builtin types of input file:

- :class:`aiogram.types.input_file.FSInputFile` - `uploading from file system <#upload-from-file-system>`__
- :class:`aiogram.types.input_file.BufferedInputFile` - `uploading from buffer <#upload-from-buffer>`__
- :class:`aiogram.types.input_file.URLInputFile` - `uploading from URL <#upload-from-url>`__

.. warning::

    **Be respectful to Telegram**

    Instances of `InputFile` are reusable.
    That means you can create an instance of InputFile and send it multiple times. However, Telegram does not recommend doing this. Instead, once you upload a file, save its `file_id` and reuse that later.

Upload from file system
=======================

By first step you will need to import InputFile wrapper:

.. code-block::

    from aiogram.types import FSInputFile

Then you can use it:

.. code-block::

    cat = FSInputFile("cat.png")
    agenda = FSInputFile("my-document.pdf", filename="agenda-2019-11-19.pdf")


.. autoclass:: aiogram.types.input_file.FSInputFile
    :members: __init__


Upload from buffer
==================

Files can be also passed from buffer
(For example you generate image using `Pillow <https://pillow.readthedocs.io/en/stable/>`_
and you want to send it to Telegram):

Import wrapper:

.. code-block::

    from aiogram.types import BufferedInputFile

And then you can use it:

.. code-block::

    text_file = BufferedInputFile(b"Hello, world!", filename="file.txt")

.. autoclass:: aiogram.types.input_file.BufferedInputFile
    :members: __init__

Upload from url
===============

If you need to upload a file from another server, but the direct link is bound to your server's IP,
or you want to bypass native `upload limits <https://core.telegram.org/bots/api#sending-files>`_
by URL, you can use :obj:`aiogram.types.input_file.URLInputFile`.

Import wrapper:

.. code-block::

    from aiogram.types import URLInputFile

And then you can use it:

.. code-block::

    image = URLInputFile(
        "https://www.python.org/static/community_logos/python-powered-h-140x182.png",
        filename="python-logo.png"
    )

.. autoclass:: aiogram.types.input_file.URLInputFile
    :members:
