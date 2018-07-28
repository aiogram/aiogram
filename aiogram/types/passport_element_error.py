import typing

from . import base
from . import fields


class PassportElementError(base.TelegramObject):
    """
    This object represents an error in the Telegram Passport element which was submitted that
    should be resolved by the user.

    https://core.telegram.org/bots/api#passportelementerror
    """

    source: base.String = fields.Field()
    type: base.String = fields.Field()
    message: base.String = fields.Field()


class PassportElementErrorDataField(PassportElementError):
    """
    Represents an issue in one of the data fields that was provided by the user.
    The error is considered resolved when the field's value changes.

    https://core.telegram.org/bots/api#passportelementerrordatafield
    """

    field_name: base.String = fields.Field()
    data_hash: base.String = fields.Field()

    def __init__(self, source: base.String, type: base.String, field_name: base.String,
                 data_hash: base.String, message: base.String):
        super(PassportElementErrorDataField, self).__init__(source=source, type=type, field_name=field_name,
                                                            data_hash=data_hash, message=message)


class PassportElementErrorFile(PassportElementError):
    """
    Represents an issue with a document scan.
    The error is considered resolved when the file with the document scan changes.

    https://core.telegram.org/bots/api#passportelementerrorfile
    """

    file_hash: base.String = fields.Field()

    def __init__(self, source: base.String, type: base.String, file_hash: base.String, message: base.String):
        super(PassportElementErrorFile, self).__init__(source=source, type=type, file_hash=file_hash,
                                                       message=message)


class PassportElementErrorFiles(PassportElementError):
    """
    Represents an issue with a list of scans.
    The error is considered resolved when the list of files containing the scans changes.

    https://core.telegram.org/bots/api#passportelementerrorfiles
    """

    file_hashes: typing.List[base.String] = fields.ListField()

    def __init__(self, source: base.String, type: base.String, file_hashes: typing.List[base.String],
                 message: base.String):
        super(PassportElementErrorFiles, self).__init__(source=source, type=type, file_hashes=file_hashes,
                                                        message=message)


class PassportElementErrorFrontSide(PassportElementError):
    """
    Represents an issue with the front side of a document.
    The error is considered resolved when the file with the front side of the document changes.

    https://core.telegram.org/bots/api#passportelementerrorfrontside
    """

    file_hash: base.String = fields.Field()

    def __init__(self, source: base.String, type: base.String, file_hash: base.String, message: base.String):
        super(PassportElementErrorFrontSide, self).__init__(source=source, type=type, file_hash=file_hash,
                                                            message=message)


class PassportElementErrorReverseSide(PassportElementError):
    """
    Represents an issue with the reverse side of a document.
    The error is considered resolved when the file with reverse side of the document changes.

    https://core.telegram.org/bots/api#passportelementerrorreverseside
    """

    file_hash: base.String = fields.Field()

    def __init__(self, source: base.String, type: base.String, file_hash: base.String, message: base.String):
        super(PassportElementErrorReverseSide, self).__init__(source=source, type=type, file_hash=file_hash,
                                                              message=message)


class PassportElementErrorSelfie(PassportElementError):
    """
    Represents an issue with the selfie with a document.
    The error is considered resolved when the file with the selfie changes.

    https://core.telegram.org/bots/api#passportelementerrorselfie
    """

    file_hash: base.String = fields.Field()

    def __init__(self, source: base.String, type: base.String, file_hash: base.String, message: base.String):
        super(PassportElementErrorSelfie, self).__init__(source=source, type=type, file_hash=file_hash,
                                                         message=message)
