from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QComboBox, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QWidget,
)

from core.episode_manager import EpisodeManager
from core.models import Episode


class NavBar(QWidget):
    """Navigation bar: Prev / episode counter / Next / Random / jump combo."""

    def __init__(self, episode_manager: EpisodeManager, parent=None):
        super().__init__(parent)
        self._manager = episode_manager

        self.setStyleSheet("background: #252525; border-top: 1px solid #444;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(8)

        btn_style = (
            "QPushButton { background: #3a3a3a; color: #dddddd; border: 1px solid #555; "
            "border-radius: 4px; padding: 4px 12px; font-size: 13px; }"
            "QPushButton:hover { background: #4a4a4a; }"
            "QPushButton:pressed { background: #222; }"
            "QPushButton:disabled { color: #555; }"
        )

        self._btn_prev = QPushButton("<< Prev")
        self._btn_prev.setStyleSheet(btn_style)
        self._btn_prev.clicked.connect(self._on_prev)
        layout.addWidget(self._btn_prev)

        self._counter_label = QLabel("—")
        self._counter_label.setStyleSheet(
            "color: #cccccc; font-size: 13px; min-width: 100px;"
        )
        self._counter_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._counter_label)

        self._btn_next = QPushButton("Next >>")
        self._btn_next.setStyleSheet(btn_style)
        self._btn_next.clicked.connect(self._on_next)
        layout.addWidget(self._btn_next)

        self._btn_random = QPushButton("Random")
        self._btn_random.setStyleSheet(btn_style)
        self._btn_random.clicked.connect(self._on_random)
        layout.addWidget(self._btn_random)

        layout.addStretch()

        go_label = QLabel("Go to:")
        go_label.setStyleSheet("color: #888888; font-size: 12px;")
        layout.addWidget(go_label)

        self._combo = QComboBox()
        self._combo.setStyleSheet(
            "QComboBox { background: #3a3a3a; color: #dddddd; border: 1px solid #555; "
            "border-radius: 4px; padding: 2px 8px; font-size: 12px; min-width: 160px; }"
            "QComboBox QAbstractItemView { background: #2a2a2a; color: #dddddd; }"
        )
        self._combo.currentIndexChanged.connect(self._on_combo_changed)
        layout.addWidget(self._combo)

        episode_manager.episode_changed.connect(self._on_episode_changed)

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def load_task(self):
        task = self._manager.task
        if task is None:
            return
        self._combo.blockSignals(True)
        self._combo.clear()
        for ep in task.episodes:
            self._combo.addItem(f"Ep {ep.id}: {ep.label[:40]}")
        self._combo.blockSignals(False)
        self._update_counter()
        self._update_buttons()

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_episode_changed(self, episode: Episode, index: int):
        self._combo.blockSignals(True)
        self._combo.setCurrentIndex(index)
        self._combo.blockSignals(False)
        self._update_counter()
        self._update_buttons()

    def _on_prev(self):
        self._manager.prev()

    def _on_next(self):
        self._manager.next()

    def _on_random(self):
        self._manager.random()

    def _on_combo_changed(self, index: int):
        if index >= 0:
            self._manager.go_to(index)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _update_counter(self):
        total = self._manager.total()
        current = self._manager.current_index() + 1
        self._counter_label.setText(f"Episode  {current}  /  {total}")

    def _update_buttons(self):
        total = self._manager.total()
        self._btn_prev.setEnabled(total > 1)
        self._btn_next.setEnabled(total > 1)
        self._btn_random.setEnabled(total > 1)
