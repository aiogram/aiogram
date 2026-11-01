Fixed :class:`aiogram.filters.command.CommandStart` with :code:`deep_link_encoded=True`
raising ``binascii.Error`` instead of rejecting the message when the deep-link payload
is not valid base64url (e.g. ``/start a`` or a truncated referral link). The error escaped
the filter, so the remaining handlers, such as a plain :code:`CommandStart()` fallback,
were never tried.
