"""Base module to hold the declarative base for sqlalchemy models"""

from sqlalchemy.ext.declarative import declarative_base

#: The declarative base model for SQLAlchemy models
BaseModel = declarative_base()
