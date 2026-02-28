from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.engine import Engine

from .parser import (
    build_primary_english_titles,
    iter_filtered_movies,
    iter_russian_titles,
)
from .schema import (
    create_engine_from_url,
    create_schema,
    movies_table,
    titles_localized_table,
)


LOGGER = logging.getLogger(__name__)


def _chunked(rows: Iterable[dict], chunk_size: int):
    batch: list[dict] = []
    for row in rows:
        batch.append(row)
        if len(batch) >= chunk_size:
            yield batch
            batch = []
    if batch:
        yield batch


def _insert_movies(engine: Engine, rows: list[dict]) -> None:
    if not rows:
        return
    dialect = engine.dialect.name

    insert_rows = [
        {
            "tconst": row["tconst"],
            "primaryTitle": row["primary_title"],
            "startYear": row["start_year"],
            "genres": row["genres"],
            "originalTitle": row["original_title"],
        }
        for row in rows
    ]

    with engine.begin() as conn:
        if dialect == "postgresql":
            stmt = pg_insert(movies_table).values(insert_rows)
            stmt = stmt.on_conflict_do_update(
                index_elements=[movies_table.c.tconst],
                set_={
                    "primaryTitle": stmt.excluded.primaryTitle,
                    "startYear": stmt.excluded.startYear,
                    "genres": stmt.excluded.genres,
                    "originalTitle": stmt.excluded.originalTitle,
                },
            )
            conn.execute(stmt)
            return

        if dialect == "sqlite":
            stmt = sqlite_insert(movies_table).values(insert_rows)
            stmt = stmt.on_conflict_do_update(
                index_elements=[movies_table.c.tconst],
                set_={
                    "primaryTitle": stmt.excluded.primaryTitle,
                    "startYear": stmt.excluded.startYear,
                    "genres": stmt.excluded.genres,
                    "originalTitle": stmt.excluded.originalTitle,
                },
            )
            conn.execute(stmt)
            return

        conn.execute(movies_table.insert(), insert_rows)


def _insert_titles(engine: Engine, rows: list[dict]) -> None:
    if not rows:
        return
    dialect = engine.dialect.name

    with engine.begin() as conn:
        if dialect == "postgresql":
            stmt = pg_insert(titles_localized_table).values(rows)
            stmt = stmt.on_conflict_do_nothing(
                index_elements=[
                    titles_localized_table.c.tconst,
                    titles_localized_table.c.language,
                    titles_localized_table.c.title,
                ]
            )
            conn.execute(stmt)
            return

        if dialect == "sqlite":
            stmt = sqlite_insert(titles_localized_table).values(rows)
            stmt = stmt.on_conflict_do_nothing(
                index_elements=[
                    titles_localized_table.c.tconst,
                    titles_localized_table.c.language,
                    titles_localized_table.c.title,
                ]
            )
            conn.execute(stmt)
            return

        conn.execute(titles_localized_table.insert(), rows)


def load_imdb_metadata(
    *,
    basics_tsv_path: Path,
    akas_tsv_path: Path,
    database_url: str,
    batch_size: int = 5000,
) -> dict[str, int]:
    engine = create_engine_from_url(database_url)
    try:
        create_schema(engine)

        movie_count = 0
        english_title_count = 0
        russian_title_count = 0

        movies_cache: list[dict] = []
        allowed_tconsts: set[str] = set()

        for movie in iter_filtered_movies(basics_tsv_path):
            movies_cache.append(movie)
            allowed_tconsts.add(movie["tconst"])

            if len(movies_cache) >= batch_size:
                _insert_movies(engine, movies_cache)
                movie_count += len(movies_cache)

                en_rows = list(build_primary_english_titles(movies_cache))
                _insert_titles(engine, en_rows)
                english_title_count += len(en_rows)
                movies_cache = []

        if movies_cache:
            _insert_movies(engine, movies_cache)
            movie_count += len(movies_cache)

            en_rows = list(build_primary_english_titles(movies_cache))
            _insert_titles(engine, en_rows)
            english_title_count += len(en_rows)

        LOGGER.info("Inserted/updated movies: %s", movie_count)
        LOGGER.info("Inserted english primary titles: %s", english_title_count)

        ru_batch: list[dict] = []
        for localized in iter_russian_titles(akas_tsv_path, allowed_tconsts):
            ru_batch.append(localized)
            if len(ru_batch) >= batch_size:
                _insert_titles(engine, ru_batch)
                russian_title_count += len(ru_batch)
                ru_batch = []

        if ru_batch:
            _insert_titles(engine, ru_batch)
            russian_title_count += len(ru_batch)

        LOGGER.info("Inserted russian localized titles: %s", russian_title_count)

        return {
            "movies": movie_count,
            "titles_en": english_title_count,
            "titles_ru": russian_title_count,
        }
    finally:
        engine.dispose()
