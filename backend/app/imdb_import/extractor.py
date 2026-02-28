from __future__ import annotations

import gzip
import logging
import shutil
from pathlib import Path


LOGGER = logging.getLogger(__name__)


def _extract_single_archive(
    *,
    archive_path: Path,
    destination_path: Path,
    overwrite: bool = False,
) -> Path:
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    if destination_path.exists() and not overwrite:
        LOGGER.info("Using cached extracted file: %s", destination_path)
        return destination_path

    LOGGER.info("Extracting %s -> %s", archive_path, destination_path)
    with gzip.open(archive_path, "rb") as gz_stream:
        with open(destination_path, "wb") as output_stream:
            shutil.copyfileobj(gz_stream, output_stream, length=1024 * 1024)

    return destination_path


def extract_archives(
    *,
    archives: dict[str, Path],
    output_dir: Path,
    overwrite: bool = False,
) -> dict[str, Path]:
    extracted: dict[str, Path] = {}
    output_dir.mkdir(parents=True, exist_ok=True)

    for filename, archive_path in archives.items():
        destination_name = filename.removesuffix(".gz")
        destination_path = output_dir / destination_name
        extracted[destination_name] = _extract_single_archive(
            archive_path=archive_path,
            destination_path=destination_path,
            overwrite=overwrite,
        )

    return extracted

