"""Module to hold the history schema and it's sub schemas."""

import json
import platform
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from command_line_assistant.constants import VERSION


@dataclass(frozen=True)
class QueryData:
    """Schema to represent a query emited by the user.

    Attributes:
        text (Optional[str], optional): The user text
        role (str): The role of the user. Defaults to "user".
    """

    text: Optional[str] = None
    role: str = "user"


@dataclass(frozen=True)
class ResponseData:
    """Schema to represent the LLM response.

    Attributes:
        text (Optional[str], optional): The LLM response
        tokens (Optional[int], optional): Amount of tokens consumed in the message.
        role (str): The role of the response. Defaults to "assistant".
    """

    text: Optional[str] = None
    tokens: Optional[int] = 0
    role: str = "assistant"


@dataclass(frozen=True)
class InteractionData:
    """Schema to represent the interaction data between user and LLM.

    Attributes:
        query (QueryData): The query data representation
        response (ResponseData): The response data representation
    """

    query: QueryData = field(default_factory=QueryData)
    response: ResponseData = field(default_factory=ResponseData)


@dataclass(frozen=True)
class OSInfo:
    """Schema to represent the system information

    Attributes:
        distribution (str): The system distribution name. Defaults to "RHEL".
        version (str): The version of the system. Defaults to `py:platform.version()`
        arch (str): The architecture of the system. Defaults to `py:platform.architecture()`
    """

    distribution: str = "RHEL"
    version: str = platform.version()
    arch: str = platform.architecture()[0]


@dataclass(frozen=True)
class EntryMetadata:
    """Schema to represent the entry metadata information

    Attributes:
        session_id (str): An unique identifier to the session. Defaults to `py:uuid.uuid4()`
        os_info (OSInfo): The system information
    """

    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    os_info: OSInfo = field(default_factory=OSInfo)


@dataclass(frozen=True)
class HistoryEntry:
    """Schema to represent an entry of the history

    Attributes:
        id (str): An unique identifier for this entry. Defaults to `py:uuid.uuid4()`
        timestamp (str): The datetime (UTC) in iso format for the entry
        interaction (InteractionData): Instance of an interaction for the entry
        metadata (EntryMetadata): Instance of entry metadata
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    # NOTE(r0x0d): This way of getting the timestamp is deprecated in newer
    # Python versions, however, the correct method is not available in Python 3.9.
    # This would be the replacement datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    interaction: InteractionData = field(default_factory=InteractionData)
    metadata: EntryMetadata = field(default_factory=EntryMetadata)

    def to_dict(self) -> dict:
        """Helper method to transform the currenty entry in dictionary.

        Returns:
            dict: Dictionary containing the information of the schema
        """
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "interaction": {
                "query": vars(self.interaction.query),
                "response": vars(self.interaction.response),
            },
            "metadata": {
                "session_id": self.metadata.session_id,
                "os_info": vars(self.metadata.os_info),
            },
        }


@dataclass
class HistoryMetadata:
    """Schema to represent the history metadata

    Attributes:
        last_updated (str): The datetime (UTC) in iso format for the last update
        version (str): The current program version. Defaults to `py:VERSION`
        entry_count (int): Quantity of entries added to the history
        size_bytes (int): The size of all entries in bytes
    """

    # NOTE(r0x0d): This way of getting the timestamp is deprecated in newer
    # Python versions, however, the correct method is not available in Python 3.9.
    # This would be the replacement datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    last_updated: str = field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z"
    )
    version: str = VERSION
    entry_count: int = 0
    size_bytes: int = 0


@dataclass
class History:
    """Schema to represent the current user history

    Attributes:
        history (list[HistoryEntry]): A list of each entry in the history
        metadata (HistoryMetadata): The metadata for the current history
    """

    history: list[HistoryEntry] = field(default_factory=list)
    metadata: HistoryMetadata = field(default_factory=HistoryMetadata)

    def to_json(self) -> str:
        """Helper method to transform current instance to json

        Returns:
            str: A valid json from the current class
        """
        return json.dumps(
            {
                "history": [entry.to_dict() for entry in self.history],
                "metadata": vars(self.metadata),
            },
            indent=2,
        )

    @classmethod
    def from_json(cls, json_str: str) -> "History":
        """Helper method to convert a json string to a History instance

        Args:
            json_str (str): The json string to be converted

        Returns:
            History: The instance of this schema converted from json
        """
        data = json.loads(json_str)
        history = []

        for entry_data in data["history"]:
            query = QueryData(**entry_data["interaction"]["query"])
            response = ResponseData(**entry_data["interaction"]["response"])
            interaction = InteractionData(query=query, response=response)

            os_info = OSInfo(**entry_data["metadata"]["os_info"])
            metadata = EntryMetadata(
                session_id=entry_data["metadata"]["session_id"],
                os_info=os_info,
            )

            entry = HistoryEntry(
                id=entry_data["id"],
                timestamp=entry_data["timestamp"],
                interaction=interaction,
                metadata=metadata,
            )
            history.append(entry)

        metadata = HistoryMetadata(**data["metadata"])
        return cls(history=history, metadata=metadata)
