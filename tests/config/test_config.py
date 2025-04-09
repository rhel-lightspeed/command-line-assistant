import sys

import pytest

from command_line_assistant import config

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


@pytest.fixture
def get_config_template(tmp_path) -> str:
    return f"""\
[database]
type = "sqlite"
connection_string = "{tmp_path / "history.db"}"

[history]
enabled = true

[backend]
endpoint = "https://localhost"

[backend.auth]
verify_ssl = true

[logging]
level = "INFO"
"""


def test_load_config_file(tmp_path, monkeypatch, get_config_template):
    config_file_path = tmp_path
    config_file = config_file_path / "command-line-assistant" / "config.toml"
    config_file.parent.mkdir()
    config_file.write_text(get_config_template)

    monkeypatch.setattr(config, "get_xdg_config_path", lambda: config_file_path)
    instance = config.load_config_file()

    assert isinstance(instance, config.Config)

    assert instance.history.enabled


def test_load_config_file_not_found(tmp_path, monkeypatch):
    config_file = tmp_path / "whatever"
    monkeypatch.setattr(config, "get_xdg_config_path", lambda: config_file)

    with pytest.raises(FileNotFoundError):
        config.load_config_file()


def test_load_config_file_decoded_error(tmp_path, monkeypatch):
    config_file_path = tmp_path
    config_file = config_file_path / "command-line-assistant" / "config.toml"
    config_file.parent.mkdir()
    config_file.write_text("""
[output]
enforce_script = False
                           """)

    monkeypatch.setattr(config, "get_xdg_config_path", lambda: config_file_path)

    with pytest.raises(tomllib.TOMLDecodeError):
        config.load_config_file()
