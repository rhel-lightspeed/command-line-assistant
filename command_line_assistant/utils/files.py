"""Utilitary module to handle file operations"""

import errno
import fcntl
import logging
import mimetypes
import os
import stat
import tempfile
from io import TextIOWrapper
from pathlib import Path
from typing import Optional, Union

from command_line_assistant.utils.environment import get_xdg_state_path

logger = logging.getLogger(__name__)


def guess_mimetype(attachment: Optional[TextIOWrapper]) -> str:
    """Guess the mimetype of a given attachment.

    Arguments:
        attachment (Optional[TextIOWrapper]): The attachment to be checked for mimetype.

    Returns:
        str: The guessed mimetype or "unknown/unknown" if not found.
    """
    unknown_mimetype = "unknown/unknown"

    if not attachment:
        return unknown_mimetype

    path = Path(attachment.name)
    result = mimetypes.guess_type(path)

    mimetype = result[0]
    if not mimetype:
        return unknown_mimetype

    return mimetype


def create_folder(path: Path, parents: bool = False, mode: int = 0o700) -> None:
    """Try to create a new folder under the specified directory.

    Notes:
        If the folder already exists, we will skip the directory creation and
        log an info message. That "check" is done by catching the
        `py:FileExistsError` and `py:FileNotFoundError` exceptions.

    Arguments:
        path (Path): The path of the folder that needs to be created.
        parents (bool): If it should create the parents folder from the given path.
        mode (int): The permissions of the given folder. Defaults to 0700.
    """
    try:
        if not path.exists():
            logger.debug(
                "Directory %s does not exist. Creating it with permissions %s",
                path,
                mode,
            )

        path.mkdir(mode=mode, parents=parents)
    except (FileExistsError, FileNotFoundError) as e:
        logger.info(
            "Skipping directory creation at '%s' as we found an exception %s. It's possible that the folder already exists or is a race condition.",
            path,
            str(e),
        )


def write_file(contents: Union[str, bytes], path: Path, mode: int = 0o600) -> None:
    """Try to write contents to a given file

    Notes:
        If the folder already exists, we will skip the file creation and
        log an info message. That "check" is done by catching the
        `py:FileExistsError` and `py:FileNotFoundError` exceptions.

    Arguments:
        contents (Union[str, bytes]): The contents that will be written to the file. Either bytes or str are expected.
        path (Path): The path of the file that needs to be created.
        mode (int): The permissions of the given file. Defaults to 0600.
    """
    try:
        logger.debug(
            "File %s does not exist. Creating it with permissions %s", path, mode
        )

        if isinstance(contents, bytes):
            path.write_bytes(contents)
        else:
            path.write_text(contents)

        path.chmod(mode)
    except (FileExistsError, FileNotFoundError) as e:
        logger.info(
            "Skipping file creation at '%s' as we found an exception %s. It's possible that the file already exists or is a race condition.",
            path,
            str(e),
        )


class NamedFileLock:
    """File-based lock mechanism for general locking purposes.

    This class provides a way to track state across processes
    using a lock file. The lock file contains the PID of the capturing process.

    Usage:
        with NamedFileLock(name="my_file") as lock:
            # Execute your operations
        # Lock is automatically released
    """

    def __init__(self, name: str) -> None:
        """Initialize the named file lock mechanism."""
        self._pid: int = os.getpid()
        self._name: str = name.replace("-", "_")
        self._lock_file: Path = Path(get_xdg_state_path(), name + ".lock")

    @property
    def pid(self) -> int:
        """Return the parent pid."""
        return self._pid

    @pid.setter
    def pid(self, value: int) -> None:
        """Set the value for the internal _pid property."""
        self._pid = value

    @property
    def is_locked(self) -> bool:
        """Check if a lock is currently active.

        This checks if the lock file exists and if the PID in it is still running.

        Returns:
            bool: True if a lock is active, False otherwise
        """
        if not self._lock_file.exists():
            return False

        try:
            pid = int(self._lock_file.read_text().strip())
            # Check if process is still running. Sending signal 0 to a process
            # will raise an OSError if no process with that pid is running.
            os.kill(pid, 0)
            return True
        except (ValueError, FileNotFoundError):
            # Clean up stale lock file
            self._lock_file.unlink(missing_ok=True)
            return False

    def acquire(self) -> None:
        """Acquire the lock.

        Raises:
            RuntimeError: If a lock is already active
        """
        if self.is_locked:
            raise RuntimeError(
                "A lock is already active in another process. "
                "Please, remove the lock before trying to acquire again."
            )

        create_folder(self._lock_file.parent, parents=True)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".pid", prefix=self._name, dir=self._lock_file.parent
        ) as handler:
            # Write current process ID
            handler.write(str(os.getpid()))
            handler.flush()

            # stat.S_IRUSR = Owner has read permission
            # stat.S_IWUSR = Owner has write permission
            os.chmod(handler.name, stat.S_IRUSR | stat.S_IWUSR)
            # Use fcntl for file locking
            fcntl.flock(handler.file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

            try:
                os.link(handler.name, self._lock_file)
            except FileExistsError as e:
                if e.errno != errno.EEXIST:
                    raise

    def release(self) -> None:
        """Release the terminal lock."""
        self._lock_file.unlink(missing_ok=True)

    def __enter__(self) -> "NamedFileLock":
        """Context manager entry.

        Returns:
            NamedFileLock: Instance of itself
        """
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.release()
