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

    result: io.BytesIO = await bot.download_file(file_path)


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
