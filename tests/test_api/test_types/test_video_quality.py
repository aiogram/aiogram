import pytest

from aiogram.types import Video, VideoQuality


@pytest.fixture()
def video_quality():
    return VideoQuality(
        file_id="abc123",
        file_unique_id="unique123",
        width=1920,
        height=1080,
        codec="h264",
    )


class TestVideoQuality:
    def test_instantiation(self, video_quality: VideoQuality):
        assert video_quality.file_id == "abc123"
        assert video_quality.file_unique_id == "unique123"
        assert video_quality.width == 1920
        assert video_quality.height == 1080
        assert video_quality.codec == "h264"
        assert video_quality.file_size is None

    def test_instantiation_with_file_size(self):
        file_size = 1048576
        vq = VideoQuality(
            file_id="abc123",
            file_unique_id="unique123",
            width=1920,
            height=1080,
            codec="h265",
            file_size=file_size,
        )
        assert vq.file_size == file_size

    def test_video_with_qualities(self, video_quality: VideoQuality):
        file_size = 524288
        video = Video(
            file_id="video123",
            file_unique_id="unique_video123",
            width=1920,
            height=1080,
            duration=120,
            qualities=[
                video_quality,
                VideoQuality(
                    file_id="q2",
                    file_unique_id="uq2",
                    width=1280,
                    height=720,
                    codec="h264",
                    file_size=file_size,
                ),
            ],
        )
        assert video.qualities is not None
        assert len(video.qualities) == 2
        assert video.qualities[0].width == 1920
        assert video.qualities[1].file_size == file_size
