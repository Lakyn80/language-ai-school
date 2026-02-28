from __future__ import annotations

import csv
from pathlib import Path
from typing import Generator


TITLE_TYPES = {"movie", "tvSeries"}
RU_LANGUAGE_CODE = "ru"
EN_LANGUAGE_CODE = "en"


def _parse_year(value: str) -> int | None:
    if value == r"\N" or not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _parse_genres(value: str) -> str | None:
    if value == r"\N" or not value:
        return None
    return value


def iter_filtered_movies(basics_tsv_path: Path) -> Generator[dict, None, None]:
    with open(basics_tsv_path, "r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            title_type = row.get("titleType", "")
            is_adult = row.get("isAdult", "")
            if title_type not in TITLE_TYPES:
                continue
            if is_adult != "0":
                continue

            tconst = row.get("tconst", "")
            primary_title = row.get("primaryTitle", "")
            original_title = row.get("originalTitle", "")
            if not tconst or not primary_title:
                continue

            yield {
                "tconst": tconst,
                "primary_title": primary_title,
                "start_year": _parse_year(row.get("startYear", "")),
                "genres": _parse_genres(row.get("genres", "")),
                "original_title": original_title or primary_title,
            }


def iter_russian_titles(
    akas_tsv_path: Path,
    allowed_tconsts: set[str],
) -> Generator[dict, None, None]:
    with open(akas_tsv_path, "r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            tconst = row.get("titleId", "")
            if not tconst or tconst not in allowed_tconsts:
                continue

            language = row.get("language", "")
            title = row.get("title", "")
            if language != RU_LANGUAGE_CODE:
                continue
            if not title or title == r"\N":
                continue

            yield {
                "tconst": tconst,
                "language": RU_LANGUAGE_CODE,
                "title": title,
            }


def build_primary_english_titles(
    movies: list[dict],
) -> Generator[dict, None, None]:
    for movie in movies:
        yield {
            "tconst": movie["tconst"],
            "language": EN_LANGUAGE_CODE,
            "title": movie["primary_title"],
        }

