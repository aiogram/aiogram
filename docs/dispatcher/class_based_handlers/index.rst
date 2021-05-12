====================
Class based handlers
====================

A handler is a async callable which takes a event with contextual data and returns a response.

In **aiogram** it can be more than just an async function, these allow you to use classes
which can be used as Telegram event handlers to structure your event handlers and reuse code by harnessing inheritance and mixins.

There are some base class based handlers what you need to use in your own handlers:

.. toctree::

    base
    callback_query
    chosen_inline_result
    error
    inline_query
    message
    poll
    pre_checkout_query
    shipping_query
    chat_member
