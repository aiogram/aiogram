.. _serialization-tool:

=============================
Telegram object serialization
=============================

Serialization
=============

To serialize Python object to Telegram object you can use pydantic serialization methods, for example:

.. code-block:: python

    message_data = { ... }  # Some message data as dict
    message = Message.model_validate(message_data)

If you want to bind serialized object to the Bot instance, you can use context:

.. code-block:: python

    message_data = { ... }  # Some message data as dict
    message = Message.model_validate(message_data, context={"bot": bot})


Deserialization
===============

In cases when you need to deserialize Telegram object to Python object, you can use this module.

To convert Telegram object to Python object excluding files you can use
:func:`aiogram.utils.serialization.deserialize_telegram_object_to_python` function.

.. autofunction:: aiogram.utils.serialization.deserialize_telegram_object_to_python

To convert Telegram object to Python object including files you can use
:func:`aiogram.utils.serialization.deserialize_telegram_object` function,
which returns :class:`aiogram.utils.serialization.DeserializedTelegramObject` object.

.. autofunction:: aiogram.utils.serialization.deserialize_telegram_object

.. autoclass:: aiogram.utils.serialization.DeserializedTelegramObject
    :members:
