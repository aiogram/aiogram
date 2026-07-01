from typing import Annotated, TypeAlias

from pydantic import Field

from .input_story_content_photo import InputStoryContentPhoto
from .input_story_content_video import InputStoryContentVideo

InputStoryContentUnion: TypeAlias = Annotated[
    InputStoryContentPhoto | InputStoryContentVideo, Field(discriminator="type")
]
