from __future__ import annotations

import argparse
import logging
from pathlib import Path

from app.imdb_import.downloader import download_imdb_archives
from app.imdb_import.extractor import extract_archives


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download and extract IMDb public datasets.")
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=Path("app/data/imdb/raw"),
        help="Directory for downloaded .gz files",
    )
    parser.add_argument(
        "--extracted-dir",
        type=Path,
        default=Path("app/data/imdb/extracted"),
        help="Directory for extracted .tsv files",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite already downloaded/extracted files",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    archives = download_imdb_archives(
        output_dir=args.raw_dir,
        overwrite=args.overwrite,
    )
    extracted = extract_archives(
        archives=archives,
        output_dir=args.extracted_dir,
        overwrite=args.overwrite,
    )

    print("Downloaded archives:")
    for name, path in archives.items():
        print(f"- {name}: {path}")

    print("\nExtracted files:")
    for name, path in extracted.items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()

