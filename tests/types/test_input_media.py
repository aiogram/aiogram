from aiogram import types
from .dataset import AUDIO, ANIMATION, \
    DOCUMENT, PHOTO, VIDEO


WIDTH = 'width'
HEIGHT = 'height'

input_media_audio = types.InputMediaAudio(
    types.Audio(**AUDIO))
input_media_animation = types.InputMediaAnimation(
    types.Animation(**ANIMATION))
input_media_document = types.InputMediaDocument(
    types.Document(**DOCUMENT))
input_media_video = types.InputMediaVideo(
    types.Video(**VIDEO))
input_media_photo = types.InputMediaPhoto(
    types.PhotoSize(**PHOTO))


def test_field_width():
    """
    https://core.telegram.org/bots/api#inputmedia
    """
    assert not hasattr(input_media_audio, WIDTH)
    assert not hasattr(input_media_document, WIDTH)
    assert not hasattr(input_media_photo, WIDTH)

    assert hasattr(input_media_animation, WIDTH)
    assert hasattr(input_media_video, WIDTH)


def test_field_height():
    """
    https://core.telegram.org/bots/api#inputmedia
    """
    assert not hasattr(input_media_audio, HEIGHT)
    assert not hasattr(input_media_document, HEIGHT)
    assert not hasattr(input_media_photo, HEIGHT)

    assert hasattr(input_media_animation, HEIGHT)
    assert hasattr(input_media_video, HEIGHT)
