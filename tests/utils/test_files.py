import pytest

from command_line_assistant.utils.files import create_folder, guess_mimetype, write_file


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


@pytest.mark.parametrize(
    ("path", "mode", "expected"),
    (
        ("test", 0o700, "700"),
        ("another-test", None, "700"),
        ("another-another-path", 0o600, "600"),
    ),
)
def test_create_folder(path, mode, expected, tmp_path):
    folder_path = tmp_path / path
    if mode:
        create_folder(folder_path, mode=mode)
    else:
        create_folder(folder_path)

    assert oct(folder_path.stat().st_mode).endswith(expected)


def test_create_folder_with_parents(tmp_path):
    folder_path = tmp_path / "test/test"
    create_folder(folder_path, parents=True)

    assert folder_path.exists()
    assert folder_path.parent.exists()


def test_create_folder_already_exists(tmp_path, caplog):
    folder_path = tmp_path / "test"
    folder_path.mkdir()
    create_folder(folder_path)

    assert "Skipping directory creation at" in caplog.records[-1].message


@pytest.mark.parametrize(
    ("contents", "path", "mode", "expected_mode"),
    (
        ("str test", "test-file.log", 0o600, "0600"),
        (b"bytes test", "test-file.log", 0o600, "0600"),
        ("test no mode", "test-file.log", None, "0600"),
    ),
)
def test_write_file(contents, path, mode, expected_mode, tmp_path):
    test_file = tmp_path / path
    if mode:
        write_file(contents, test_file, mode)
    else:
        write_file(contents, test_file)

    assert oct(test_file.stat().st_mode).endswith(expected_mode)
