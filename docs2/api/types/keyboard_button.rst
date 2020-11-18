##############
KeyboardButton
##############

This object represents one button of the reply keyboard. For simple text buttons String can be used instead of this object to specify text of the button. Optional fields request_contact, request_location, and request_poll are mutually exclusive.

Note: request_contact and request_location options will only work in Telegram versions released after 9 April, 2016. Older clients will display unsupported message.

Note: request_poll option will only work in Telegram versions released after 23 January, 2020. Older clients will display unsupported message.

.. automodule:: aiogram.types.keyboard_button
    :members:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True