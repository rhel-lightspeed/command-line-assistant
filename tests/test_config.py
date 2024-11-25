import json
from pathlib import Path

import pytest

from command_line_assistant import config

# tomllib is available in the stdlib after Python3.11. Before that, we import
# from tomli.
try:
    import tomllib  # pyright: ignore[reportMissingImports]
except ImportError:
    import tomli as tomllib  # pyright: ignore[reportMissingImports]


@pytest.mark.parametrize(
    ("schema",),
    (
        (config.LoggingSchema,),
        (config.OutputSchema,),
        (config.BackendSchema,),
        (config.HistorySchema,),
    ),
)
def test_initialize_schemas(schema):
    # Making sure that we don't error out while initializing the schema with default vlaues.
    assert isinstance(schema(), schema)


def test_invalid_logging_type():
    with pytest.raises(TypeError, match="Logging type invalid is not available."):
        config.LoggingSchema(type="invalid")


def test_create_config_file(tmp_path):
    config_file = Path(tmp_path / "test" / "config.toml")

    config._create_config_file(config_file)

    assert config_file.exists()
    assert config_file.read_text()


@pytest.fixture
def working_config_mapping():
    """Fixture that represent a working config template"""
    return {
        "enforce_script": json.dumps(True),
        "output_file": "invalid-path",
        "prompt_separator": "$",
        "enabled": json.dumps(True),
        "history_file": "invalid-path",
        "max_size": 10,
        "endpoint": "http://test",
        "verify_ssl": json.dumps(False),
        "logging_type": "minimal",
    }


def test_read_config_file(tmp_path, working_config_mapping):
    config_file_template = config.CONFIG_TEMPLATE

    config_formatted = config_file_template.format_map(working_config_mapping)

    config_file = tmp_path / "config.toml"
    config_file.write_text(config_formatted)

    _config = config._read_config_file(config_file)

    assert _config.history
    assert _config.backend
    assert _config.output
    assert _config.logging


def test_read_config_file_invalid_toml(tmp_path):
    config_file_template = config.CONFIG_TEMPLATE

    mapping = {
        "enforce_script": True,
        "output_file": "invalid-path",
        "prompt_separator": "$",
        "enabled": True,
        "history_file": "invalid-path",
        "max_size": 10,
        "endpoint": "http://test",
        "verify_ssl": False,
        "logging_type": "minimal",
    }

    config_formatted = config_file_template.format_map(mapping)

    config_file = tmp_path / "config.toml"
    config_file.write_text(config_formatted)

    with pytest.raises(tomllib.TOMLDecodeError, match="Invalid value"):
        config._read_config_file(config_file)


def test_read_config_file_not_found():
    config_file = Path("a-file.toml")
    with pytest.raises(FileNotFoundError):
        config._read_config_file(config_file)


def test_load_config_file(tmp_path):
    """The config_file does not exist, so we create one through this workflow."""
    config_file = tmp_path / "cla" / "config.toml"
    new_config = config.load_config_file(config_file)
    assert new_config == config.Config()


def test_load_existing_config_file(tmp_path, working_config_mapping):
    """The config_file exist, so we read the file instead of creating one."""
    config_file_template = config.CONFIG_TEMPLATE

    config_formatted = config_file_template.format_map(working_config_mapping)

    config_file = tmp_path / "config.toml"
    config_file.write_text(config_formatted)

    existing_config = config.load_config_file(config_file)
    assert isinstance(existing_config, config.Config)
    assert existing_config.backend
    assert existing_config.output
    assert existing_config.history
    assert existing_config.logging
