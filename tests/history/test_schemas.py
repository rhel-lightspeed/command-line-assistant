import json
from datetime import datetime

import pytest

from command_line_assistant.history.schemas import (
    EntryMetadata,
    History,
    HistoryEntry,
    HistoryMetadata,
    InteractionData,
    OSInfo,
    QueryData,
    ResponseData,
)


def test_query_data_initialization():
    """Test QueryData initialization and defaults"""
    query = QueryData()
    assert query.text is None
    assert query.context is None
    assert query.role == "user"

    # Test with values
    query = QueryData(text="test query", context="some context", role="custom")
    assert query.text == "test query"
    assert query.context == "some context"
    assert query.role == "custom"


def test_response_data_initialization():
    """Test ResponseData initialization and defaults"""
    response = ResponseData()
    assert response.text is None
    assert response.tokens == 0
    assert response.role == "assistant"

    # Test with values
    response = ResponseData(text="test response", tokens=42, role="custom")
    assert response.text == "test response"
    assert response.tokens == 42
    assert response.role == "custom"


def test_interaction_data_initialization():
    """Test InteractionData initialization and defaults"""
    interaction = InteractionData()
    assert isinstance(interaction.query, QueryData)
    assert isinstance(interaction.response, ResponseData)

    # Test with custom query and response
    query = QueryData(text="test query")
    response = ResponseData(text="test response")
    interaction = InteractionData(query=query, response=response)
    assert interaction.query.text == "test query"
    assert interaction.response.text == "test response"


def test_os_info_initialization():
    """Test OSInfo initialization and defaults"""
    os_info = OSInfo()
    assert os_info.distribution == "RHEL"
    assert isinstance(os_info.version, str)
    assert isinstance(os_info.arch, str)

    # Test with custom values
    os_info = OSInfo(distribution="Ubuntu", version="22.04", arch="x86_64")
    assert os_info.distribution == "Ubuntu"
    assert os_info.version == "22.04"
    assert os_info.arch == "x86_64"


def test_entry_metadata_initialization():
    """Test EntryMetadata initialization"""
    metadata = EntryMetadata()
    assert isinstance(metadata.session_id, str)
    assert isinstance(metadata.os_info, OSInfo)

    # Verify UUID format
    import uuid

    uuid.UUID(metadata.session_id)  # Should not raise exception


def test_history_entry_initialization():
    """Test HistoryEntry initialization and to_dict method"""
    entry = HistoryEntry()
    assert isinstance(entry.id, str)
    assert isinstance(entry.timestamp, str)
    assert isinstance(entry.interaction, InteractionData)
    assert isinstance(entry.metadata, EntryMetadata)


def test_history_entry_to_dict():
    """Test HistoryEntry to_dict conversion"""
    entry = HistoryEntry()
    entry.interaction.query.text = "test query"
    entry.interaction.response.text = "test response"

    entry_dict = entry.to_dict()
    assert isinstance(entry_dict, dict)
    assert entry_dict["interaction"]["query"]["text"] == "test query"
    assert entry_dict["interaction"]["response"]["text"] == "test response"
    assert "id" in entry_dict
    assert "timestamp" in entry_dict
    assert "metadata" in entry_dict


def test_history_metadata_initialization():
    """Test HistoryMetadata initialization"""
    metadata = HistoryMetadata()
    assert isinstance(metadata.last_updated, str)
    assert isinstance(metadata.version, str)
    assert metadata.entry_count == 0
    assert metadata.size_bytes == 0


def test_history_initialization():
    """Test History initialization"""
    history = History()
    assert isinstance(history.history, list)
    assert len(history.history) == 0
    assert isinstance(history.metadata, HistoryMetadata)


def test_history_json_serialization():
    """Test History to_json and from_json methods"""
    # Create a history with some test data
    history = History()
    entry = HistoryEntry()
    entry.interaction.query.text = "test query"
    entry.interaction.response.text = "test response"
    history.history.append(entry)

    # Convert to JSON
    json_str = history.to_json()
    assert isinstance(json_str, str)

    # Parse JSON string to verify structure
    parsed = json.loads(json_str)
    assert "history" in parsed
    assert "metadata" in parsed
    assert len(parsed["history"]) == 1

    # Convert back from JSON
    new_history = History.from_json(json_str)
    assert isinstance(new_history, History)
    assert len(new_history.history) == 1
    assert new_history.history[0].interaction.query.text == "test query"
    assert new_history.history[0].interaction.response.text == "test response"


def test_history_with_multiple_entries():
    """Test History with multiple entries"""
    history = History()

    # Add multiple entries
    entries = [
        ("query1", "response1"),
        ("query2", "response2"),
        ("query3", "response3"),
    ]

    for query_text, response_text in entries:
        entry = HistoryEntry()
        entry.interaction.query.text = query_text
        entry.interaction.response.text = response_text
        history.history.append(entry)

    # Verify entries
    assert len(history.history) == len(entries)
    for i, (query_text, response_text) in enumerate(entries):
        assert history.history[i].interaction.query.text == query_text
        assert history.history[i].interaction.response.text == response_text


def test_history_json_roundtrip_with_special_characters():
    """Test History JSON serialization with special characters"""
    history = History()
    entry = HistoryEntry()
    entry.interaction.query.text = "test\nquery with 'special' \"characters\" & symbols"
    entry.interaction.response.text = "response\twith\nspecial\rcharacters"
    history.history.append(entry)

    # Roundtrip through JSON
    json_str = history.to_json()
    new_history = History.from_json(json_str)

    assert new_history.history[0].interaction.query.text == entry.interaction.query.text
    assert (
        new_history.history[0].interaction.response.text
        == entry.interaction.response.text
    )


@pytest.mark.parametrize("invalid_json", ["", "{}", '{"invalid": "data"}'])
def test_history_from_json_with_invalid_data(invalid_json):
    """Test History.from_json with invalid JSON data"""
    with pytest.raises((KeyError, json.JSONDecodeError)):
        History.from_json(invalid_json)


def test_history_entry_timestamp_format():
    """Test that HistoryEntry timestamps are in the correct format"""
    entry = HistoryEntry()
    # Verify the timestamp is in ISO format
    try:
        datetime.fromisoformat(entry.timestamp.rstrip("Z"))
    except ValueError:
        pytest.fail("Timestamp is not in valid ISO format")
