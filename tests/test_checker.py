from shorts_qc.checker import (
    check_audio_present,
    check_duration,
    check_frame_rate,
    check_long_silence,
    check_loudness,
    check_resolution,
    check_vertical_9_16,
    parse_mean_volume,
    parse_silence_durations,
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


def test_parse_mean_volume():
    text = "[Parsed_volumedetect_0] mean_volume: -16.2 dB\n[Parsed_volumedetect_0] max_volume: -1.5 dB"
    assert parse_mean_volume(text) == -16.2
    assert parse_mean_volume("no volume here") is None


def test_parse_silence_durations():
    text = "silence_start: 1.0\nsilence_end: 3.4 | silence_duration: 2.4\nsilence_duration: 0.8"
    assert parse_silence_durations(text) == [2.4, 0.8]
    assert parse_silence_durations("nothing") == []


def test_long_silence():
    assert check_long_silence(0.5).passed
    assert check_long_silence(2.0).passed
    assert not check_long_silence(2.4).passed
    r = check_long_silence(None)
    assert r.passed and r.skipped
