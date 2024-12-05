import pytest

from command_line_assistant.utils import environment


@pytest.mark.parametrize(
    ("xdg_path_env", "expected"),
    (
        ("", "/etc/xdg"),
        ("/etc/xdg", "/etc/xdg"),
        ("/etc/xdg:some/other/path", "/etc/xdg"),
        ("no-path-xdg:what-iam-doing", "/etc/xdg"),
        ("/my-special-one-path", "/my-special-one-path"),
    ),
)
def test_get_xdg_path(xdg_path_env, expected, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_DIRS", xdg_path_env)
    assert environment.get_xdg_path() == expected
