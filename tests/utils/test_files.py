import os
from pathlib import Path
from unittest import mock

import pytest

from command_line_assistant.utils.files import (
    NamedFileLock,
    create_folder,
    guess_mimetype,
    write_file,
)


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


def test_write_file_permission_error(tmp_path, monkeypatch):
    """Test write_file behavior with permission errors"""
    test_file = tmp_path / "test.txt"

    # Mock Path.write_text to raise PermissionError
    def mock_write_text(self, content):
        raise PermissionError("Permission denied")

    monkeypatch.setattr(Path, "write_text", mock_write_text)

    # Should log error and continue without raising exception
    with pytest.raises(PermissionError):
        write_file("test content", test_file)


class TestNamedFileLock:
    def test_acquire(self, mock_xdg_path):
        lock = NamedFileLock(name="test")
        lock.acquire()

        expected_pid = os.getpid()
        expected_path = Path(mock_xdg_path, "test.lock")
        assert os.path.exists(expected_path)
        assert int(expected_path.read_text()) == expected_pid

    def test_acquire_as_context_manager(self, mock_xdg_path):
        with NamedFileLock(name="test"):
            expected_pid = os.getpid()
            expected_path = Path(mock_xdg_path, "test.lock")
            assert os.path.exists(expected_path)
            assert int(expected_path.read_text()) == expected_pid

        # After we leave the context manager, the file should be gone.
        assert not os.path.exists(expected_path)

    def test_acquire_multiple_locks(self, mock_xdg_path):
        lock_names = ["test", "terminal", "files", "star-trek"]

        for lock_name in lock_names:
            lock = NamedFileLock(name=lock_name)
            lock.acquire()

        expected_pid = os.getpid()

        assert len(os.listdir(mock_xdg_path)) == len(lock_names)

        for lock_name in lock_names:
            expected_path = Path(mock_xdg_path, f"{lock_name}.lock")
            assert os.path.exists(expected_path)
            assert int(expected_path.read_text()) == expected_pid

    def test_acquire_twice_same_lock(self, mock_xdg_path):
        lock = NamedFileLock(name="test")
        lock.acquire()

        expected_pid = os.getpid()
        expected_path = Path(mock_xdg_path, "test.lock")
        assert os.path.exists(expected_path)
        assert int(expected_path.read_text()) == expected_pid

        with pytest.raises(
            RuntimeError,
            match="A lock is already active in another process. "
            "Please, remove the lock before trying to acquire again.",
        ):
            lock.acquire()

    def test_is_locked_success(self, mock_xdg_path):
        lock = NamedFileLock(name="test")
        lock.acquire()

        expected_path = Path(mock_xdg_path, "test.lock")
        assert os.path.exists(expected_path)
        assert lock.is_locked

    def test_is_locked_file_not_exist(self):
        lock = NamedFileLock(name="test")
        assert not lock.is_locked

    def test_is_locked_exception(self, mock_xdg_path, monkeypatch):
        monkeypatch.setattr(os, "kill", mock.Mock(side_effect=ValueError("oh no.")))

        lock = NamedFileLock(name="test")
        lock.acquire()

        expected_path = Path(mock_xdg_path, "test.lock")
        assert not lock.is_locked
        assert not os.path.exists(expected_path)

    def test_release_lock(self, mock_xdg_path):
        lock = NamedFileLock(name="test")
        lock.acquire()
        lock.release()

        expected_path = Path(mock_xdg_path, "test.lock")
        assert not os.path.exists(expected_path)
