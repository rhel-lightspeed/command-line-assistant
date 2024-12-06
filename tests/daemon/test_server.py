from unittest import mock

from command_line_assistant.config import Config
from command_line_assistant.dbus import server


def test_serve(monkeypatch):
    event_loop_mock = mock.Mock()
    session_bus_mock = mock.Mock()
    monkeypatch.setattr(server, "EventLoop", event_loop_mock)
    monkeypatch.setattr(server, "SESSION_BUS", session_bus_mock)
    config = Config()

    server.serve(config)

    assert event_loop_mock.call_count == 1
