#####################
How to download file?
#####################

Download file manually
======================

First, you must get the `file_id` of the file you want to download.
Information about files sent to the bot is contained in `Message <types/message.html>`__.

For example, download the document that came to the bot.

.. code-block::

    file_id = message.document.file_id

Then use the `getFile <methods/get_file.html>`__ method to get `file_path`.

.. code-block::

    file = await bot.get_file(file_id)
    file_path = file.file_path

After that, use the `download_file <#download-file>`__ method from the bot object.

download_file(...)
------------------

Download file by `file_path` to destination.

If you want to automatically create destination (:obj:`io.BytesIO`) use default
value of destination and handle result of this method.

.. automethod:: aiogram.client.bot.Bot.download_file

There are two options where you can download the file: to **disk** or to **binary I/O object**.

Download file to disk
---------------------

To download file to disk, you must specify the file name or path where to download the file.
In this case, the function will return nothing.

.. code-block::

    await bot.download_file(file_path, "text.txt")

Download file to binary I/O object
----------------------------------

To download file to binary I/O object, you must specify an object with the
:obj:`typing.BinaryIO` type or use the default (:obj:`None`) value.

In the first case, the function will return your object:

.. code-block::

    my_object = MyBinaryIO()
    result: MyBinaryIO = await bot.download_file(file_path, my_object)
    # print(result is my_object)  # True

If you leave the default value, an :obj:`io.BytesIO` object will be created and returned.

.. code-block::

    result = await bot.download_file(file_path)

Type checkers see the difference: with a path destination the return type is :code:`None`,
with a binary I/O object it is the type of that object, and with the default it is
:obj:`typing.BinaryIO`.


Download file in short way
==========================

Getting `file_path` manually every time is boring, so you should use the `download <#download>`__ method.

download(...)
-------------

Download file by `file_id` or `Downloadable` object to destination.

If you want to automatically create destination (:obj:`io.BytesIO`) use default
value of destination and handle result of this method.

.. automethod:: aiogram.client.bot.Bot.download

It differs from `download_file <#download-file>`__ **only** in that it accepts `file_id`
or an `Downloadable` object (object that contains the `file_id` attribute) instead of `file_path`.

You can download a file to `disk <#download-file-to-disk>`__ or to a `binary I/O <#download-file-to-binary-io-object>`__ object in the same way.

Example:

.. code-block::

    document = message.document
    await bot.download(document)


Stream a file
=============

To process a file chunk by chunk without keeping it whole, use the `stream <#stream>`__ method.
It accepts a `file_id` or a `Downloadable` object, like `download <#download>`__.

stream(...)
-----------

.. automethod:: aiogram.client.bot.Bot.stream

.. code-block::

    async with bot.stream(message.document, chunk_size=65536) as stream:
        async for chunk in stream:
            hasher.update(chunk)

Nothing is requested before the first chunk is read. The connection is released when the file
ends or reading fails; :code:`async with` (or :code:`await stream.aclose()`) also releases it at
once when the loop stops early with :code:`break` or an exception.

.. autoclass:: aiogram.client.bot.DownloadStream
    :members: aclose


Timeouts
========

Downloads have per-phase timeouts instead of one total timeout: a large file on a slow link
finishes, and a transfer that stops sending data fails.

.. autoclass:: aiogram.client.session.base.DownloadTimeout
    :members: of

By default (:code:`DownloadTimeout()`) getting a connection may take 30 seconds and the server may
stay silent for 60 seconds between two reads; the whole download has no limit. Pass your own value
to :code:`download`, :code:`download_file` or :code:`stream`:

.. code-block::

    from aiogram.client.session.base import DownloadTimeout

    await bot.download(document, "file.bin", timeout=DownloadTimeout(sock_read=120, total=3600))

A plain number keeps the old meaning, a total timeout in seconds: :code:`timeout=5` is
:code:`DownloadTimeout(connect=None, sock_read=None, total=5)`. A failed or timed-out download
raises :class:`~aiogram.exceptions.TelegramNetworkError`.

A custom session whose :code:`stream_content` still declares :code:`timeout: int = 30` keeps
working: it receives the total timeout, or 30 seconds when there is none, and aiogram emits one
:obj:`DeprecationWarning` per session class. To receive a :class:`DownloadTimeout`, declare
:code:`timeout: DownloadTimeout | float = DEFAULT_DOWNLOAD_TIMEOUT`
(both from :code:`aiogram.client.session.base`).
