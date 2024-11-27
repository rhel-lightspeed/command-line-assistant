import json

import pytest

from command_line_assistant import config

# tomllib is available in the stdlib after Python3.11. Before that, we import
# from tomli.
try:
    import tomllib  # pyright: ignore[reportMissingImports]
except ImportError:
    import tomli as tomllib  # noqa: F401  # pyright: ignore[reportMissingImports]


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
        "logging_verbose": json.dumps(True),
    }


def test_load_existing_config_file(tmp_path, working_config_mapping, monkeypatch):
    """The config_file exist, so we read the file instead of creating one."""
    config_file_template = config.CONFIG_TEMPLATE
    config_formatted = config_file_template.format_map(working_config_mapping)

    config_file = tmp_path / "config.toml"
    config_file.write_text(config_formatted)
    monkeypatch.setattr(config, "CONFIG_DEFAULT_PATH", config_file)

    existing_config = config.load_config_file()
    assert isinstance(existing_config, config.Config)
    assert existing_config.backend
    assert existing_config.output
    assert existing_config.history
    assert existing_config.logging
