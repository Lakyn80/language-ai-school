from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


LOGGER = logging.getLogger(__name__)

IMDB_BASE_URL = "https://datasets.imdbws.com"
IMDB_FILES = (
    "title.basics.tsv.gz",
    "title.akas.tsv.gz",
)


def _download_file(
    *,
    url: str,
    destination: Path,
    retries: int = 3,
    timeout_seconds: int = 120,
) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)

    attempt = 0
    while True:
        attempt += 1
        try:
            with urlopen(url, timeout=timeout_seconds) as response:
                with open(destination, "wb") as output:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        output.write(chunk)
            return destination
        except (HTTPError, URLError, TimeoutError) as exc:
            if attempt >= retries:
                raise RuntimeError(f"Failed to download {url}: {exc}") from exc
            sleep_seconds = min(2**attempt, 10)
            LOGGER.warning(
                "Download failed for %s (attempt %s/%s): %s. Retrying in %ss",
                url,
                attempt,
                retries,
                exc,
                sleep_seconds,
            )
            time.sleep(sleep_seconds)


def download_imdb_archives(
    *,
    output_dir: Path,
    filenames: Iterable[str] = IMDB_FILES,
    overwrite: bool = False,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    downloaded: dict[str, Path] = {}

    for filename in filenames:
        url = f"{IMDB_BASE_URL}/{filename}"
        destination = output_dir / filename
        if destination.exists() and not overwrite:
            LOGGER.info("Using cached archive: %s", destination)
            downloaded[filename] = destination
            continue

        LOGGER.info("Downloading %s -> %s", url, destination)
        downloaded[filename] = _download_file(url=url, destination=destination)

    return downloaded

