import pytest

from univid.compress import MIN_VIDEO_KBPS, TooLarge, plan_encode

MB10 = 10 * 1024 * 1024


def test_short_clip_keeps_full_resolution():
    video, audio, height = plan_encode(15, MB10)
    assert audio == 128
    assert height is None
    assert video > 2500


def test_medium_clip_scales_down():
    _, audio, height = plan_encode(60, MB10)
    assert audio == 128
    assert height == 720


def test_long_clip_drops_to_480_and_low_audio():
    video, audio, height = plan_encode(300, MB10)
    assert audio == 64
    assert height == 480
    assert video >= MIN_VIDEO_KBPS


def test_fits_budget():
    for duration in (10, 60, 200):
        video, audio, _ = plan_encode(duration, MB10)
        assert (video + audio) * 1000 / 8 * duration <= MB10


def test_too_long_raises():
    with pytest.raises(TooLarge):
        plan_encode(900, MB10)


def test_boosted_server_allows_longer():
    plan_encode(900, 50 * 1024 * 1024)
