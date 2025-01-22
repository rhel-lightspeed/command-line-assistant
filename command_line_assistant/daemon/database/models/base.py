"""Base module to hold the declarative base for sqlalchemy models"""

import uuid
from typing import Any

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.type_api import TypeEngine
from sqlalchemy.types import CHAR, TypeDecorator

#: The declarative base model for SQLAlchemy models
BaseModel = declarative_base()


class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses PostgreSQL's UUID type, otherwise uses CHAR(32), storing as
    stringified hex values.

    This is a workaround for RHEL 9 and SQLAlchemy 1.4.45, as in that version
    we don't have UUID generic type, so this class is needed to emulate that
    behavior.

    Attributes:
        impl (TypeEngine): Required attribute by SQLAlchemy to reference any :class:`.TypeEngine` class.
        cache_ok (bool): Indicates if this class is safe to be used as part of cache key.

    Reference:
        https://gist.github.com/gmolveau/7caeeefe637679005a7bb9ae1b5e421e
    """

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect: Dialect) -> TypeEngine[Any]:
        """Load the dialect implementation

        Args:
            dialect (Dialect): Instance of a dialect class to be used.

        Returns:
            TypeEngine: An object corresponding to the dialect selected
        """
        type_descriptor = UUID() if dialect.name == "postgresql" else CHAR(32)
        return dialect.type_descriptor(type_descriptor)

    def process_bind_param(self, value: Any, dialect: Dialect) -> Any:
        """Receive a literal parameter value to be rendered inline within a statement.

        Args:
            value (Any): The parameter value
            dialect (Dialect): Instance of a dialect class to be used.

        Returns:
            Any: Instance of a str, hexstring or the value itself
        """

        if value is None:
            return value
        elif dialect.name == "postgresql":
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value).int
            else:
                # hexstring
                return "%.32x" % value.int

    def _uuid_value(self, value: Any) -> Any:
        """Internal method to convert to UUID value.

        Args:
            value (Any): The parameter value

        Returns:
            Any: Either will be a UUID instance, str or Any value.

        """
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                value = uuid.UUID(value)
            return value

    def process_result_value(self, value: Any, dialect: Dialect) -> Any:
        """Process the resulting value

        Args:
            value (Any): The parameter value
            dialect (Dialect): Instance of a dialect class to be used.

        Returns:
            Any: Any value returned by the internal _uuid_value method
        """
        return self._uuid_value(value)
