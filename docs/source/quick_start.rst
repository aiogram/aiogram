===========
Quick start
===========

Simple template
---------------

At first you have to import all necessary modules

.. literalinclude:: ../../examples/echo_bot.py
    :language: python
    :lines: 6-8

Then you have to initialize bot and dispatcher instances.
Bot token you can get from `@BotFather <https://t.me/BotFather>`_

.. literalinclude:: ../../examples/echo_bot.py
    :language: python
    :lines: 10-17

Next step: interaction with bots starts with one command. Register your first command handler:

.. literalinclude:: ../../examples/echo_bot.py
    :language: python
    :lines: 21-25

If you want to handle all messages in the chat simply add handler without filters:

.. literalinclude:: ../../examples/echo_bot.py
    :language: python
    :lines: 28-30

Last step: run long polling.

.. literalinclude:: ../../examples/echo_bot.py
    :language: python
    :lines: 33-34

Summary
-------

.. literalinclude:: ../../examples/echo_bot.py
    :language: python
    :linenos:
    :lines: -19,27-
