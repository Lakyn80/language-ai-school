from __future__ import annotations

from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
)
from sqlalchemy.engine import Engine


metadata = MetaData()

movies_table = Table(
    "movies",
    metadata,
    Column("tconst", String(16), primary_key=True),
    Column("primaryTitle", Text, nullable=False),
    Column("startYear", Integer, nullable=True),
    Column("genres", Text, nullable=True),
    Column("originalTitle", Text, nullable=False),
)

titles_localized_table = Table(
    "titles_localized",
    metadata,
    Column("tconst", String(16), ForeignKey("movies.tconst", ondelete="CASCADE"), primary_key=True),
    Column("language", String(8), primary_key=True),
    Column("title", Text, primary_key=True),
)


def create_engine_from_url(database_url: str) -> Engine:
    return create_engine(database_url, pool_pre_ping=True, future=True)


def create_schema(engine: Engine) -> None:
    metadata.create_all(engine)

