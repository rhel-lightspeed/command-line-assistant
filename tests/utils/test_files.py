import pytest

from command_line_assistant.utils.files import guess_mimetype


def test_guess_mimetype():
    assert guess_mimetype(None) == "unknown/unknown"


@pytest.mark.parametrize(
    ("file", "mimetype"),
    (
        ("file.txt", "text/plain"),
        ("file.csv", "text/csv"),
        ("file.json", "application/json"),
        ("file.jpg", "image/jpeg"),
        ("file.mp3", "audio/mpeg"),
        ("file.mp4", "video/mp4"),
        ("file.pdf", "application/pdf"),
        ("file.zip", "application/zip"),
        ("file", "unknown/unknown"),
    ),
)
def test_guess_mimetype_file_extension(file, mimetype, tmp_path):
    file_path = tmp_path / file
    file_path.touch()
    assert guess_mimetype(file_path.open()) == mimetype
