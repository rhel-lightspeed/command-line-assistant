"""Session management module for the daemon."""

import logging
import uuid
from pathlib import Path
from typing import Optional, Union

#: Path to the machine ID file
MACHINE_ID_PATH: Path = Path("/etc/machine-id")

logger = logging.getLogger(__name__)


class UserSessionManager:
    """Manage user session information."""

    def __init__(self, effective_user_id: Union[int, str]) -> None:
        """Initialize the session manager.

        Args:
            effective_user_id (Union[int, str]): The effective user id
        """
        self._effective_user_id: Union[int, str] = effective_user_id
        self._machine_uuid: Optional[uuid.UUID] = None
        self._user_id: Optional[uuid.UUID] = None

    @property
    def machine_id(self) -> uuid.UUID:
        """Property that holds the machine UUID.

        Reference:
            https://www.freedesktop.org/software/systemd/man/latest/machine-id.html

        Raises:
            FileNotFoundError: If the machine-id file doesn't exist
            ValueError: If the machine-id file is empty or malformed

        Returns:
            uuid.UUID: The UUID generated from machine-id
        """
        if not self._machine_uuid:
            try:
                machine_id = MACHINE_ID_PATH.read_text().strip()
                if not machine_id:
                    logger.error("Machine ID file is empty")
                    raise ValueError(f"Machine ID at {MACHINE_ID_PATH} is empty")
                # Create a UUID from the machine-id string
                self._machine_uuid = uuid.UUID(machine_id)
            except FileNotFoundError as e:
                logger.error("Machine ID file not found at %s", MACHINE_ID_PATH)
                raise FileNotFoundError(
                    f"Machine ID file not found at {MACHINE_ID_PATH}"
                ) from e

        return self._machine_uuid

    @property
    def user_id(self) -> uuid.UUID:
        """Property that generates a unique user ID combining machine and user effective id.

        Returns:
            uuid.UUID: A unique session identifier
        """
        if not self._user_id:
            # Combine machine ID and effective user to create a unique namespace
            namespace = self.machine_id

            # Generate a UUID using the effective username as name in the namespace
            self._user_id = uuid.uuid5(namespace, str(self._effective_user_id))

        return self._user_id
