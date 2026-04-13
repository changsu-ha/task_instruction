from __future__ import annotations
import csv
import json
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from core.models import Episode, LogEntry


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


class SessionLogger:
    """Append-only JSONL logger for episode collection sessions.

    One log file per session (identified by session_id UUID).
    Supports CSV and JSON full exports.
    """

    def __init__(self, task_name: str, log_dir: Path):
        self.task_name = task_name
        self.session_id = str(uuid.uuid4())
        log_dir.mkdir(parents=True, exist_ok=True)
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in task_name)
        self._log_path = log_dir / f"{safe_name}_{self.session_id[:8]}.jsonl"
        self._entries: Dict[int, LogEntry] = {}   # episode_id -> LogEntry

    # ------------------------------------------------------------------
    # Episode lifecycle
    # ------------------------------------------------------------------

    def start_episode(self, episode: Episode):
        entry = LogEntry(
            episode_id=episode.id,
            task_name=self.task_name,
            status="pending",
            start_time=_now_iso(),
            session_id=self.session_id,
            config_snapshot={
                "label": episode.label,
                "objects": [
                    {
                        "id": obj.id,
                        "type": obj.type,
                        "x_cm": obj.x_cm,
                        "y_cm": obj.y_cm,
                        "rotation_deg": obj.rotation_deg,
                        "label": obj.label,
                        "description": obj.description,
                    }
                    for obj in episode.objects
                ],
            },
        )
        self._entries[episode.id] = entry

    def end_episode(self, episode_id: int, status: str, operator_notes: str = ""):
        entry = self._entries.get(episode_id)
        if entry is None:
            return
        entry.status = status
        entry.operator_notes = operator_notes
        entry.end_time = _now_iso()
        if entry.start_time:
            try:
                start = datetime.fromisoformat(entry.start_time)
                end = datetime.fromisoformat(entry.end_time)
                entry.duration_seconds = round((end - start).total_seconds(), 2)
            except Exception:
                pass
        self._append_record(entry)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def get_summary(self) -> Dict[str, int]:
        counts: Dict[str, int] = {"collected": 0, "skipped": 0, "retry": 0, "pending": 0}
        for entry in self._entries.values():
            key = entry.status if entry.status in counts else "pending"
            counts[key] += 1
        return counts

    def get_status(self, episode_id: int) -> str:
        entry = self._entries.get(episode_id)
        return entry.status if entry else "pending"

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export_csv(self, output_path: Path):
        fields = [
            "session_id", "task_name", "episode_id", "status",
            "start_time", "end_time", "duration_seconds", "operator_notes",
        ]
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            for entry in sorted(self._entries.values(), key=lambda e: e.episode_id):
                row = asdict(entry)
                row.pop("config_snapshot", None)
                writer.writerow(row)

    def export_json(self, output_path: Path):
        summary = self.get_summary()
        summary["total"] = len(self._entries)
        export_data = {
            "export_time": _now_iso(),
            "session_id": self.session_id,
            "task": {"name": self.task_name},
            "summary": summary,
            "episodes": [
                asdict(entry)
                for entry in sorted(self._entries.values(), key=lambda e: e.episode_id)
            ],
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

    @property
    def log_path(self) -> Path:
        return self._log_path

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _append_record(self, entry: LogEntry):
        record = asdict(entry)
        with open(self._log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
