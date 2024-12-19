import pytest

from command_line_assistant import config

# tomllib is available in the stdlib after Python3.11. Before that, we import
# from tomli.
try:
    import tomllib  # pyright: ignore[reportMissingImports]
except ImportError:
    import tomli as tomllib  # pyright: ignore[reportMissingImports]


@pytest.fixture
def get_config_template(tmp_path) -> str:
    output_file = tmp_path / "output.tmp"
    history_file = tmp_path / "history.json"

    return f"""\
[output]
# otherwise recording via script session will be enforced
enforce_script = true
# file with output(s) of regular commands (e.g. ls, echo, etc.)
file = "{output_file}"
# Keep non-empty if your file contains only output of commands (not prompt itself)
prompt_separator = "$"

[history]
enabled = true
file = "{history_file}"
# max number of queries in history (including responses)

[backend]
endpoint = "https://localhost"

[backend.auth]
verify_ssl = true

[logging]
level = "INFO"
"""


def test_load_config_file(tmp_path, monkeypatch, get_config_template):
    config_file_path = tmp_path
    config_file = config_file_path / "command_line_assistant" / "config.toml"
    config_file.parent.mkdir()
    config_file.write_text(get_config_template)

    monkeypatch.setattr(config, "get_xdg_config_path", lambda: config_file_path)
    instance = config.load_config_file()

    assert isinstance(instance, config.Config)

    assert instance.output.enforce_script
    assert instance.history.enabled


def test_load_config_file_not_found(tmp_path, monkeypatch):
    config_file = tmp_path / "whatever"
    monkeypatch.setattr(config, "get_xdg_config_path", lambda: config_file)

    with pytest.raises(FileNotFoundError):
        config.load_config_file()


def test_load_config_file_decoded_error(tmp_path, monkeypatch):
    config_file_path = tmp_path
    config_file = config_file_path / "command_line_assistant" / "config.toml"
    config_file.parent.mkdir()
    config_file.write_text("""
[output]
enforce_script = False
                           """)

    monkeypatch.setattr(config, "get_xdg_config_path", lambda: config_file_path)

    with pytest.raises(tomllib.TOMLDecodeError):
        config.load_config_file()
