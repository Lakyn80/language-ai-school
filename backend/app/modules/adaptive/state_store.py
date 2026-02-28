import json
from pathlib import Path
from threading import Lock
from typing import Any


DEFAULT_DATA_ROOT = Path(__file__).resolve().parents[2] / "data"
DEFAULT_RUNS_DIR = DEFAULT_DATA_ROOT / "adaptive_runs"
DEFAULT_HISTORY_DIR = DEFAULT_DATA_ROOT / "adaptive_history"


class FileStateStore:
    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or DEFAULT_RUNS_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()

    def _state_path(self, run_id: str) -> Path:
        return self.base_dir / f"{run_id}.json"

    def save_state(self, run_id: str, state: dict[str, Any]) -> None:
        path = self._state_path(run_id)
        with self._lock:
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(state, handle, ensure_ascii=False, indent=2)

    def load_state(self, run_id: str) -> dict[str, Any] | None:
        path = self._state_path(run_id)
        if not path.exists():
            return None

        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)


class FileHistoryStore:
    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or DEFAULT_HISTORY_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()

    def _history_path(self, student_id: str) -> Path:
        safe_student_id = student_id.replace("/", "_").replace("\\", "_")
        return self.base_dir / f"{safe_student_id}.json"

    def load_student_history(self, student_id: str) -> dict[str, Any]:
        path = self._history_path(student_id)
        if not path.exists():
            return {"records": []}

        with open(path, "r", encoding="utf-8") as handle:
            records = json.load(handle)
        if not isinstance(records, list):
            return {"records": []}
        return {"records": records}

    def append_student_history(self, student_id: str, record: dict[str, Any]) -> None:
        path = self._history_path(student_id)
        with self._lock:
            if path.exists():
                with open(path, "r", encoding="utf-8") as handle:
                    records = json.load(handle)
                if not isinstance(records, list):
                    records = []
            else:
                records = []

            records.append(record)

            with open(path, "w", encoding="utf-8") as handle:
                json.dump(records, handle, ensure_ascii=False, indent=2)
