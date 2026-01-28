import json
from pathlib import Path

DATA_PATH = Path(__file__).parent / "data" / "titles.json"


def load_titles():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
