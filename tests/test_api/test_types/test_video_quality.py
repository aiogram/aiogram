from aiogram.types import Video, VideoQuality


class TestVideoQuality:
    def test_instantiation(self):
        vq = VideoQuality(
            file_id="abc123",
            file_unique_id="unique123",
            width=1920,
            height=1080,
            codec="h264",
        )
        assert vq.file_id == "abc123"
        assert vq.file_unique_id == "unique123"
        assert vq.width == 1920
        assert vq.height == 1080
        assert vq.codec == "h264"
        assert vq.file_size is None

    def test_instantiation_with_file_size(self):
        vq = VideoQuality(
            file_id="abc123",
            file_unique_id="unique123",
            width=1920,
            height=1080,
            codec="h265",
            file_size=1048576,
        )
        assert vq.file_size == 1048576

    def test_video_with_qualities(self):
        video = Video(
            file_id="video123",
            file_unique_id="unique_video123",
            width=1920,
            height=1080,
            duration=120,
            qualities=[
                VideoQuality(
                    file_id="q1",
                    file_unique_id="uq1",
                    width=1920,
                    height=1080,
                    codec="h264",
                ),
                VideoQuality(
                    file_id="q2",
                    file_unique_id="uq2",
                    width=1280,
                    height=720,
                    codec="h264",
                    file_size=524288,
                ),
            ],
        )
        assert video.qualities is not None
        assert len(video.qualities) == 2
        assert video.qualities[0].width == 1920
        assert video.qualities[1].file_size == 524288
