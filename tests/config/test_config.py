from pathlib import Path

import pytest

from command_line_assistant import config

# tomllib is available in the stdlib after Python3.11. Before that, we import
# from tomli.
try:
    import tomllib  # pyright: ignore[reportMissingImports]
except ImportError:
    import tomli as tomllib  # pyright: ignore[reportMissingImports]


def test_load_config_file(tmpdir, monkeypatch):
    config_file = tmpdir.join("config.toml")

    config_file.write("""
[output]
enforce_script = true

[history]
enabled = true

[backend]
verify_ssl = true

[logging]
verbose = true
                      """)

    monkeypatch.setattr(config, "CONFIG_DEFAULT_PATH", Path(config_file))
    instance = config.load_config_file()

    assert isinstance(instance, config.Config)

    assert instance.output.enforce_script
    assert instance.history.enabled
    assert instance.backend.verify_ssl
    assert instance.logging.verbose


def test_load_config_file_not_found(tmpdir, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_DEFAULT_PATH", Path(tmpdir.join("test.toml")))

    with pytest.raises(FileNotFoundError):
        config.load_config_file()


def test_load_config_file_decoded_error(tmpdir, monkeypatch):
    config_file = tmpdir.join("test.toml")
    config_file.write("""
[output]
enforce_script = True
                      """)
    monkeypatch.setattr(config, "CONFIG_DEFAULT_PATH", Path(config_file))

    with pytest.raises(tomllib.TOMLDecodeError):
        config.load_config_file()
