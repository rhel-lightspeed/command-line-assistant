"""Session management module for the daemon."""

import logging
import uuid
from pathlib import Path
from typing import Optional

#: Path to the machine ID file
MACHINE_ID_PATH: Path = Path("/etc/machine-id")

logger = logging.getLogger(__name__)


class UserSessionManager:
    """Manage user session information."""

    def __init__(self) -> None:
        """Initialize the session manager."""
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

    def get_user_id(self, effective_user_id: int) -> str:
        """Get the user ID based on the effective user ID.

        Arguments:
            effective_user_id (int): The effective user ID

        Returns:
            str: The user ID
        """
        if not self._user_id:
            # Combine machine ID and effective user to create a unique namespace
            namespace = self.machine_id

            # Generate a UUID using the effective username as name in the namespace
            self._user_id = uuid.uuid5(namespace, str(effective_user_id))

        return str(self._user_id)
