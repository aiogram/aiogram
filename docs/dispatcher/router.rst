######
Router
######

.. autoclass:: aiogram.dispatcher.router.Router
    :members: __init__, include_router
    :show-inheritance:


Event observers
===============

.. warning::

    All handlers always should be asynchronous.
    The name of the handler function is not important. The event argument name is also not important but it is recommended to not overlap the name with contextual data in due to function can not accept two arguments with the same name.

Here is the list of available observers and examples of how to register handlers

In these examples only decorator-style registering handlers are used, but if you don't like @decorators just use :obj:`<event type>.register(...)` method instead.

Update
------

.. code-block:: python

    @router.update()
    async def message_handler(update: types.Update) -> Any: pass

.. note::

    By default Router already has an update handler which route all event types to another observers.


Message
-------


.. attention::

    Be attentive with filtering this event

    You should expect that this event can be with different sets of attributes in different cases

    (For example text, sticker and document are always of different content types of message)

    Recommended way to check field availability before usage, for example via :ref:`magic filter <magic-filters>`:
    :code:`F.text` to handle text, :code:`F.sticker` to handle stickers only and etc.


.. code-block:: python

    @router.message()
    async def message_handler(message: types.Message) -> Any: pass


Edited message
--------------

.. code-block:: python

    @router.edited_message()
    async def edited_message_handler(edited_message: types.Message) -> Any: pass

Channel post
------------

.. code-block:: python

    @router.channel_post()
    async def channel_post_handler(channel_post: types.Message) -> Any: pass

Edited channel post
-------------------

.. code-block:: python

    @router.edited_channel_post()
    async def edited_channel_post_handler(edited_channel_post: types.Message) -> Any: pass


Inline query
------------

.. code-block:: python

    @router.inline_query()
    async def inline_query_handler(inline_query: types.Message) -> Any: pass

Chosen inline query
-------------------

.. code-block:: python

    @router.chosen_inline_result()
    async def chosen_inline_result_handler(chosen_inline_result: types.ChosenInlineResult) -> Any: pass

Callback query
--------------

.. code-block:: python

    @router.callback_query()
    async def callback_query_handler(callback_query: types.CallbackQuery) -> Any: pass

Shipping query
--------------

.. code-block:: python

    @router.shipping_query()
    async def shipping_query_handler(shipping_query: types.ShippingQuery) -> Any: pass

Pre checkout query
------------------

.. code-block:: python

    @router.pre_checkout_query()
    async def pre_checkout_query_handler(pre_checkout_query: types.PreCheckoutQuery) -> Any: pass

Poll
----

.. code-block:: python

    @router.poll()
    async def poll_handler(poll: types.Poll) -> Any: pass

Poll answer
-----------

.. code-block:: python

    @router.poll_answer()
    async def poll_answer_handler(poll_answer: types.PollAnswer) -> Any: pass

Errors
------

.. code-block:: python

    @router.errors()
    async def error_handler(exception: ErrorEvent) -> Any: pass

Is useful for handling errors from other handlers


Nested routers
==============

.. warning::

    Routers by the way can be nested to an another routers with some limitations:
        1. Router **CAN NOT** include itself
        1. Routers **CAN NOT** be used for circular including (router 1 include router 2, router 2 include router 3, router 3 include router 1)


Example:

.. code-block:: python
    :caption: module_2.py
    :name: module_2

    router2 = Router()

    @router2.message()
    ...


.. code-block:: python
    :caption: module_2.py
    :name: module_1

    from module_2 import router2


    router1 = Router()
    router1.include_router(router2)


How it works?
-------------

For example, dispatcher has 2 routers, the last router also has one nested router:

.. image:: ../_static/nested_routers_example.png
    :alt: Nested routers example

In this case update propagation flow will have form:

.. image:: ../_static/update_propagation_flow.png
    :alt: Nested routers example
