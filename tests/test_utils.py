import pytest
from vericlient.utils import get_virtual_file


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
