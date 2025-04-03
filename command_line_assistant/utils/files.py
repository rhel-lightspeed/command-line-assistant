"""Utilitary module to handle file operations"""

import logging
import mimetypes
from io import TextIOWrapper
from pathlib import Path
from typing import Optional, Union

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
