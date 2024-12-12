from pathlib import Path

import pytest

from command_line_assistant.utils import environment


@pytest.mark.parametrize(
    ("xdg_path_env", "expected"),
    (
        ("", Path("/etc/xdg")),
        ("/etc/xdg", Path("/etc/xdg")),
        ("/etc/xdg:some/other/path", Path("/etc/xdg")),
        ("no-path-xdg:what-iam-doing", Path("/etc/xdg")),
        ("/my-special-one-path", Path("/my-special-one-path")),
    ),
)
def test_get_xdg_config_path(xdg_path_env, expected, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("XDG_CONFIG_DIRS", xdg_path_env)
    assert environment.get_xdg_config_path() == expected


@pytest.mark.parametrize(
    ("xdg_path_env", "expected"),
    (
        ("", Path("some/dir")),
        ("/etc/xdg", Path("/etc/xdg")),
        ("/my-special-one-path", Path("/my-special-one-path")),
    ),
)
def test_get_xdg_state_path(xdg_path_env, expected, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(environment, "WANTED_XDG_STATE_PATH", Path("some/dir"))
    monkeypatch.setenv("XDG_STATE_HOME", xdg_path_env)
    assert environment.get_xdg_state_path() == expected
