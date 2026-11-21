from typing import Annotated, TypeAlias

from pydantic import Field

from .input_profile_photo_animated import InputProfilePhotoAnimated
from .input_profile_photo_static import InputProfilePhotoStatic

InputProfilePhotoUnion: TypeAlias = Annotated[
    InputProfilePhotoStatic | InputProfilePhotoAnimated, Field(discriminator="type")
]
