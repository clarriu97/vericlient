import pytest

from vericlient.utils import DEFAULT_CONTENT_TYPE, get_virtual_file, guess_content_type


def test_get_virtual_file(temp_dir):
    file_path = f"{temp_dir}/test.txt"
    with open(file_path, "wb") as f:
        f.write(b"test")
    assert get_virtual_file(file_path) == b"test"

    assert get_virtual_file(b"test") == b"test"

    with pytest.raises(TypeError):
        get_virtual_file(123)

    with pytest.raises(FileNotFoundError):
        get_virtual_file("non-existing-file.txt")


def test_guess_content_type(audio_file):
    assert guess_content_type(audio_file) == "audio/wav"  # sniffed, not platform dependent
    assert guess_content_type(b"\xff\xd8\xff\xe0rest of a jpeg") == "image/jpeg"
    assert guess_content_type(b"\x89PNG\r\n\x1a\nrest of a png") == "image/png"
    assert guess_content_type(b"\x00\x00\x00\x20ftypisom") == "video/mp4"
    assert guess_content_type(b"") == DEFAULT_CONTENT_TYPE
    assert guess_content_type(b"nothing recognisable") == DEFAULT_CONTENT_TYPE
