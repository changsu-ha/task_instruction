from __future__ import annotations
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QVBoxLayout, QWidget,
)

from core.episode_manager import EpisodeManager
from core.logger import SessionLogger
from core.models import Episode


class LogPanel(QWidget):
    """Bottom panel: notes input, status buttons, summary, and export."""

    def __init__(self, episode_manager: EpisodeManager, logger: SessionLogger, parent=None):
        super().__init__(parent)
        self._manager = episode_manager
        self._logger = logger

        self.setStyleSheet("background: #252525; border-top: 1px solid #444;")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 8, 12, 8)
        outer.setSpacing(6)

        # Notes row
        notes_row = QHBoxLayout()
        notes_label = QLabel("Notes:")
        notes_label.setStyleSheet("color: #888888; font-size: 12px;")
        notes_row.addWidget(notes_label)

        self._notes_edit = QLineEdit()
        self._notes_edit.setPlaceholderText("Optional collector notes…")
        self._notes_edit.setStyleSheet(
            "QLineEdit { background: #333; color: #dddddd; border: 1px solid #555; "
            "border-radius: 4px; padding: 3px 8px; font-size: 12px; }"
        )
        notes_row.addWidget(self._notes_edit, 1)
        outer.addLayout(notes_row)

        # Status buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        collected_style = (
            "QPushButton { background: #1e7e34; color: #ffffff; border: none; "
            "border-radius: 4px; padding: 5px 16px; font-size: 13px; font-weight: bold; }"
            "QPushButton:hover { background: #28a745; }"
        )
        skip_style = (
            "QPushButton { background: #5a5a5a; color: #dddddd; border: none; "
            "border-radius: 4px; padding: 5px 16px; font-size: 13px; }"
            "QPushButton:hover { background: #6a6a6a; }"
        )
        retry_style = (
            "QPushButton { background: #7d4e00; color: #ffffff; border: none; "
            "border-radius: 4px; padding: 5px 16px; font-size: 13px; }"
            "QPushButton:hover { background: #e67e00; }"
        )

        self._btn_collected = QPushButton("Collected")
        self._btn_collected.setStyleSheet(collected_style)
        self._btn_collected.clicked.connect(lambda: self._mark("collected"))
        btn_row.addWidget(self._btn_collected)

        self._btn_skip = QPushButton("Skip")
        self._btn_skip.setStyleSheet(skip_style)
        self._btn_skip.clicked.connect(lambda: self._mark("skipped"))
        btn_row.addWidget(self._btn_skip)

        self._btn_retry = QPushButton("Retry")
        self._btn_retry.setStyleSheet(retry_style)
        self._btn_retry.clicked.connect(lambda: self._mark("retry"))
        btn_row.addWidget(self._btn_retry)

        btn_row.addStretch()

        self._summary_label = QLabel("Collected: 0  Skip: 0  Retry: 0  Pending: 0")
        self._summary_label.setStyleSheet("color: #888888; font-size: 11px;")
        btn_row.addWidget(self._summary_label)

        btn_row.addSpacing(16)

        export_style = (
            "QPushButton { background: #2c5f8a; color: #ffffff; border: none; "
            "border-radius: 4px; padding: 5px 14px; font-size: 12px; }"
            "QPushButton:hover { background: #3b7fbf; }"
        )
        self._btn_export = QPushButton("Export…")
        self._btn_export.setStyleSheet(export_style)
        self._btn_export.clicked.connect(self._on_export)
        btn_row.addWidget(self._btn_export)

        outer.addLayout(btn_row)

        episode_manager.episode_changed.connect(self._on_episode_changed)

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def start_current_episode(self):
        episode = self._manager.current_episode()
        if episode:
            self._logger.start_episode(episode)
            self._notes_edit.clear()

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_episode_changed(self, episode: Episode, index: int):
        # Start timing the new episode
        self._logger.start_episode(episode)
        self._notes_edit.clear()
        self._update_summary()

    def _mark(self, status: str):
        episode = self._manager.current_episode()
        if episode is None:
            return
        notes = self._notes_edit.text().strip()
        self._logger.end_episode(episode.id, status, notes)
        self._update_summary()
        # Auto-advance to next episode
        self._manager.next()

    def _on_export(self):
        task_name = ""
        if self._manager.task:
            task_name = self._manager.task.name
        path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Session Log",
            str(Path.home() / f"session_export.json"),
            "JSON (*.json);;CSV (*.csv)",
        )
        if not path:
            return
        output = Path(path)
        if selected_filter.startswith("CSV") or output.suffix.lower() == ".csv":
            self._logger.export_csv(output)
        else:
            self._logger.export_json(output)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _update_summary(self):
        summary = self._logger.get_summary()
        self._summary_label.setText(
            f"Collected: {summary['collected']}  "
            f"Skip: {summary['skipped']}  "
            f"Retry: {summary['retry']}  "
            f"Pending: {summary['pending']}"
        )
