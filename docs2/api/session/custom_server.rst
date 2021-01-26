Use Custom API server
=====================

.. autoclass:: aiogram.client.telegram.TelegramAPIServer
    :members:

For example, if you want to use self-hosted API server:

.. code-block:: python3

    session = AiohttpSession()
    session.api = TelegramAPIServer.from_base('http://localhost:8082')
    bot = Bot(..., session=session)
