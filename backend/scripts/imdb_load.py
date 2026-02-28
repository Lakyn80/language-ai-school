from __future__ import annotations

import argparse
import logging
from pathlib import Path

from app.imdb_import.loader import load_imdb_metadata


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load IMDb metadata into SQL database.")
    parser.add_argument(
        "--basics-tsv",
        type=Path,
        default=Path("app/data/imdb/extracted/title.basics.tsv"),
        help="Path to extracted title.basics.tsv",
    )
    parser.add_argument(
        "--akas-tsv",
        type=Path,
        default=Path("app/data/imdb/extracted/title.akas.tsv"),
        help="Path to extracted title.akas.tsv",
    )
    parser.add_argument(
        "--database-url",
        required=True,
        help="SQLAlchemy URL (sqlite:///... or postgresql+psycopg://...)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5000,
        help="Batch size for DB inserts",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if not args.basics_tsv.exists():
        raise FileNotFoundError(f"Missing basics TSV: {args.basics_tsv}")
    if not args.akas_tsv.exists():
        raise FileNotFoundError(f"Missing akas TSV: {args.akas_tsv}")

    stats = load_imdb_metadata(
        basics_tsv_path=args.basics_tsv,
        akas_tsv_path=args.akas_tsv,
        database_url=args.database_url,
        batch_size=args.batch_size,
    )

    print("Load completed:")
    for key, value in stats.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()

