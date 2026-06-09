Use Custom API server
=====================

For example, if you want to use self-hosted API server:

.. code-block:: python

    session = AiohttpSession(
        api=TelegramAPIServer.from_base('http://localhost:8082')
    )
    bot = Bot(..., session=session)

.. autoclass:: aiogram.client.telegram.TelegramAPIServer
    :members:
