from pathlib import Path

import pytest

from command_line_assistant.config.schemas.database import DatabaseSchema


def test_database_schema_invalid_type():
    type = "NOT_FOUND_DB"
    with pytest.raises(
        ValueError, match="The database type must be one of .*, not NOT_FOUND_DB"
    ):
        DatabaseSchema(type=type)


@pytest.mark.parametrize(
    ("type", "port", "connection_string"),
    (
        ("sqlite", None, "sqlite:/test"),
        ("mysql", 3306, None),
        ("postgresql", 5432, None),
    ),
)
def test_database_schema_default_initialization(type, port, connection_string):
    result = DatabaseSchema(
        type=type,
        port=port,
        connection_string=connection_string,
        database="test",
        username="test",
        password="test",
    )

    assert result.port == port
    if connection_string:
        assert result.connection_string == Path(connection_string)
    assert result.type == type


@pytest.mark.parametrize(
    ("identifier", "value"),
    (
        ("database-username", "test"),
        ("database-password", "test"),
    ),
)
def test_read_credentials_from_systemd(identifier, value, tmp_path, monkeypatch):
    systemd_mock_path = tmp_path / identifier
    systemd_mock_path.write_text("test")
    monkeypatch.setenv("CREDENTIALS_DIRECTORY", str(tmp_path))

    schema = DatabaseSchema()
    assert schema._read_credentials_from_systemd(identifier=identifier) == value


def test_read_credentials_from_systemd_contents_empty_exception():
    schema = DatabaseSchema()
    with pytest.raises(
        ValueError,
        match="Either username or password is missing from config file or systemd-creds.",
    ):
        assert schema._read_credentials_from_systemd(identifier="testtest")


def test_read_credentials_from_systemd_file_not_found_exception(tmp_path, monkeypatch):
    systemd_mock_path = tmp_path / "test"
    monkeypatch.setenv("CREDENTIALS_DIRECTORY", str(systemd_mock_path))

    schema = DatabaseSchema()
    with pytest.raises(ValueError, match="does not exist."):
        assert schema._read_credentials_from_systemd(identifier="testtest")


def test_initialize_without_username_and_password_read_from_systemd_creds(
    tmp_path, monkeypatch
):
    systemd_mock_username_path = tmp_path / "database-username"
    systemd_mock_username_path.write_text("test")

    systemd_mock_password_path = tmp_path / "database-password"
    systemd_mock_password_path.write_text("test")

    monkeypatch.setenv("CREDENTIALS_DIRECTORY", str(tmp_path))

    schema = DatabaseSchema(type="postgresql", username=None, password=None)
    assert schema.username == "test"
    assert schema.password == "test"


def test_database_connection_string_path_expansion():
    """Test that database connection string paths are expanded"""
    # Test with tilde in path
    schema = DatabaseSchema(type="sqlite", connection_string="~/test.db")
    assert schema.connection_string.is_absolute()  # type: ignore
    assert "test.db" in str(schema.connection_string)

    # Test with relative path
    schema = DatabaseSchema(type="sqlite", connection_string="./test.db")
    assert "test.db" in str(schema.connection_string)


def test_database_get_connection_url():
    """Test database connection URL construction for different database types"""
    # SQLite
    sqlite_db = DatabaseSchema(
        type="sqlite", connection_string=Path("/path/to/db.sqlite")
    )
    assert sqlite_db.get_connection_url() == "sqlite:////path/to/db.sqlite"

    # MySQL
    mysql_db = DatabaseSchema(
        type="mysql",
        host="localhost",
        port=3306,
        database="testdb",
        username="user",
        password="pass",
    )
    assert (
        mysql_db.get_connection_url()
        == "mysql+pymysql://user:pass@localhost:3306/testdb"
    )

    # PostgreSQL
    pg_db = DatabaseSchema(
        type="postgresql",
        host="localhost",
        port=5432,
        database="testdb",
        username="user",
        password="pass",
    )
    assert pg_db.get_connection_url() == "postgresql://user:pass@localhost:5432/testdb"
