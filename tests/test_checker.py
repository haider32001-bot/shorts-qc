from shorts_qc.checker import (
    check_audio_present,
    check_duration,
    check_frame_rate,
    check_loudness,
    check_resolution,
    check_vertical_9_16,
)


def test_duration_pass_and_fail():
    assert check_duration(42.0).passed
    assert check_duration(60.0).passed
    assert not check_duration(60.1).passed


def test_vertical_9_16():
    assert check_vertical_9_16(1080, 1920).passed
    assert check_vertical_9_16(720, 1280).passed
    assert not check_vertical_9_16(1920, 1080).passed  # landscape band
    assert not check_vertical_9_16(1080, 1080).passed


def test_resolution():
    assert check_resolution(1080, 1920).passed
    assert not check_resolution(720, 1280).passed


def test_frame_rate():
    assert check_frame_rate(30.0).passed
    assert not check_frame_rate(15.0).passed


def test_audio_present():
    assert check_audio_present(1).passed
    assert not check_audio_present(0).passed


def test_loudness_skipped_when_unknown():
    r = check_loudness(None)
    assert r.passed and r.skipped
    assert not check_loudness(-40.0).passed
    assert check_loudness(-16.0).passed
