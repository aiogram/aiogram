===========
Quick start
===========

Simple template
---------------

At first you have to import all necessary modules

.. literalinclude:: ../../examples/echo_bot.py
    :language: python
    :lines: 1-4

Then you have to initialize bot and dispatcher instances.
Bot token you can get from `@BotFather <https://t.me/BotFather>`_

.. literalinclude:: ../../examples/echo_bot.py
    :language: python
    :lines: 10-12

Next step: interaction with bots starts with one command. Register your first command handler:

.. literalinclude:: ../../examples/echo_bot.py
    :language: python
    :lines: 15-17

If you want to handle all messages in the chat simply add handler without filters:

.. literalinclude:: ../../examples/echo_bot.py
    :language: python
    :lines: 27-29

Last step: run long polling.

.. literalinclude:: ../../examples/echo_bot.py
    :language: python
    :lines: 32-33

Summary
-------

.. literalinclude:: ../../examples/echo_bot.py
    :language: python
    :linenos:
    :lines: -19,27-