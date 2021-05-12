########
Observer
########

Observer is used for filtering and handling different events. That is part of internal API with some public methods and is recommended to don't use methods is not listed here.

In `aiogram` framework is available two variants of observer:

- `EventObserver <#eventobserver>`__ 
- `TelegramEventObserver <#telegrameventobserver>`__


EventObserver
=============

.. autoclass:: aiogram.dispatcher.event.event.EventObserver
    :members: register, trigger, __call__
    :member-order: bysource


TelegramEventObserver
=====================

.. autoclass:: aiogram.dispatcher.event.telegram.TelegramEventObserver
    :members: register, trigger, __call__, bind_filter, middleware, outer_middleware
    :member-order: bysource
