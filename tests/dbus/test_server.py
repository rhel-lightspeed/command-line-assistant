from unittest import mock

from command_line_assistant.config import Config
from command_line_assistant.dbus import server


def test_serve(monkeypatch, mock_config):
    event_loop_mock = mock.Mock()
    system_bus_mock = mock.Mock()
    monkeypatch.setattr(server, "EventLoop", event_loop_mock)
    monkeypatch.setattr(server, "SYSTEM_BUS", system_bus_mock)

    server.serve(mock_config)

    assert event_loop_mock.call_count == 1


def test_serve_registers_services(monkeypatch, mock_config):
    event_loop_mock = mock.Mock()
    system_bus_mock = mock.Mock()
    monkeypatch.setattr(server, "EventLoop", event_loop_mock)
    monkeypatch.setattr(server, "SYSTEM_BUS", system_bus_mock)

    server.serve(mock_config)

    assert system_bus_mock.publish_object.call_count == 3
    assert system_bus_mock.register_service.call_count == 3


def test_serve_cleanup_on_exception(monkeypatch):
    event_loop_mock = mock.Mock()
    event_loop_mock.return_value.run.side_effect = Exception("Test error")
    system_bus_mock = mock.Mock()
    monkeypatch.setattr(server, "EventLoop", event_loop_mock)
    monkeypatch.setattr(server, "SYSTEM_BUS", system_bus_mock)
    config = Config()

    try:
        server.serve(config)
    except Exception:
        pass

    system_bus_mock.disconnect.assert_called_once()


def test_serve_creates_interfaces(monkeypatch, mock_config):
    event_loop_mock = mock.Mock()
    system_bus_mock = mock.Mock()
    monkeypatch.setattr(server, "EventLoop", event_loop_mock)
    monkeypatch.setattr(server, "SYSTEM_BUS", system_bus_mock)

    server.serve(mock_config)

    publish_calls = system_bus_mock.publish_object.call_args_list
    assert len(publish_calls) == 3
    assert isinstance(publish_calls[0][0][1], server.ChatInterface)
    assert isinstance(publish_calls[1][0][1], server.HistoryInterface)
    assert isinstance(publish_calls[2][0][1], server.UserInterface)
