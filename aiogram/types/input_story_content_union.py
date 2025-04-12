from typing import Union

from .input_story_content_photo import InputStoryContentPhoto
from .input_story_content_video import InputStoryContentVideo

InputStoryContentUnion = Union[InputStoryContentPhoto, InputStoryContentVideo]
