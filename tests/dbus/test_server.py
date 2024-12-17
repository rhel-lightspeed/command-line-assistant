from unittest import mock

from dasbus.constants import DBUS_NAME_FLAG_REPLACE_EXISTING

from command_line_assistant.config import Config
from command_line_assistant.dbus import server


def test_serve(monkeypatch):
    event_loop_mock = mock.Mock()
    system_bus_mock = mock.Mock()
    monkeypatch.setattr(server, "EventLoop", event_loop_mock)
    monkeypatch.setattr(server, "SYSTEM_BUS", system_bus_mock)
    config = Config()

    server.serve(config)

    assert event_loop_mock.call_count == 1


def test_serve_registers_services(monkeypatch):
    event_loop_mock = mock.Mock()
    system_bus_mock = mock.Mock()
    monkeypatch.setattr(server, "EventLoop", event_loop_mock)
    monkeypatch.setattr(server, "SYSTEM_BUS", system_bus_mock)
    config = Config()

    server.serve(config)

    assert system_bus_mock.publish_object.call_count == 2
    assert system_bus_mock.register_service.call_count == 2
    assert (
        system_bus_mock.register_service.call_args_list[1][1]["flags"]
        == DBUS_NAME_FLAG_REPLACE_EXISTING
    )


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


def test_serve_creates_interfaces(monkeypatch):
    event_loop_mock = mock.Mock()
    system_bus_mock = mock.Mock()
    monkeypatch.setattr(server, "EventLoop", event_loop_mock)
    monkeypatch.setattr(server, "SYSTEM_BUS", system_bus_mock)
    config = Config()

    server.serve(config)

    publish_calls = system_bus_mock.publish_object.call_args_list
    assert len(publish_calls) == 2
    assert isinstance(publish_calls[0][0][1], server.QueryInterface)
    assert isinstance(publish_calls[1][0][1], server.HistoryInterface)
