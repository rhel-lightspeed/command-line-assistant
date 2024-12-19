import json
import platform
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from command_line_assistant.constants import VERSION


@dataclass
class QueryData:
    text: Optional[str] = None
    context: Optional[str] = None
    role: str = "user"


@dataclass
class ResponseData:
    text: Optional[str] = None
    tokens: Optional[int] = 0
    role: str = "assistant"


@dataclass
class InteractionData:
    query: QueryData = field(default_factory=QueryData)
    response: ResponseData = field(default_factory=ResponseData)


@dataclass
class OSInfo:
    distribution: str = "RHEL"
    version: str = platform.version()
    arch: str = platform.machine()


@dataclass
class EntryMetadata:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    os_info: OSInfo = field(default_factory=OSInfo)


@dataclass
class HistoryEntry:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    # NOTE(r0x0d): This way of getting the timestamp is deprecated in newer
    # Python versions, however, the correct method is not available in Python 3.9.
    # This would be the replacement datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    interaction: InteractionData = field(default_factory=InteractionData)
    metadata: EntryMetadata = field(default_factory=EntryMetadata)

    def to_dict(self) -> dict:
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
    history: list[HistoryEntry] = field(default_factory=list)
    metadata: HistoryMetadata = field(default_factory=HistoryMetadata)

    def to_json(self) -> str:
        return json.dumps(
            {
                "history": [entry.to_dict() for entry in self.history],
                "metadata": vars(self.metadata),
            },
            indent=2,
        )

    @classmethod
    def from_json(cls, json_str: str) -> "History":
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
