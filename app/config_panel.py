from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPainter, QPixmap
from PyQt5.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QScrollArea, QSizePolicy,
    QVBoxLayout, QWidget,
)

from core.episode_manager import EpisodeManager
from core.models import Episode, TaskConfig


def _color_icon(hex_color: str, size: int = 14) -> QPixmap:
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(hex_color))
    return pixmap


class ConfigPanel(QScrollArea):
    """Displays task name, episode info, and per-object configuration text."""

    def __init__(self, episode_manager: EpisodeManager, parent=None):
        super().__init__(parent)
        self._manager = episode_manager
        self._task_config: TaskConfig | None = None

        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setStyleSheet("background: #1e1e1e; border: none;")

        self._container = QWidget()
        self._container.setStyleSheet("background: #1e1e1e;")
        self._layout = QVBoxLayout(self._container)
        self._layout.setAlignment(Qt.AlignTop)
        self._layout.setContentsMargins(12, 12, 12, 12)
        self._layout.setSpacing(6)
        self.setWidget(self._container)

        episode_manager.episode_changed.connect(self._on_episode_changed)

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def load_task(self, task_config: TaskConfig):
        self._task_config = task_config
        episode = self._manager.current_episode()
        if episode:
            self._rebuild(episode)

    # ------------------------------------------------------------------
    # Slot
    # ------------------------------------------------------------------

    def _on_episode_changed(self, episode: Episode, index: int):
        self._rebuild(episode)

    # ------------------------------------------------------------------
    # Build UI
    # ------------------------------------------------------------------

    def _rebuild(self, episode: Episode):
        # Clear existing layout contents
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if self._task_config is None:
            return

        task = self._task_config
        total = self._manager.total()
        current = self._manager.current_index() + 1

        # Task name
        task_label = QLabel(task.name)
        task_label.setStyleSheet(
            "color: #ffffff; font-size: 15px; font-weight: bold;"
        )
        task_label.setWordWrap(True)
        self._layout.addWidget(task_label)

        # Task description
        if task.description:
            desc_label = QLabel(task.description.strip())
            desc_label.setStyleSheet("color: #aaaaaa; font-size: 11px;")
            desc_label.setWordWrap(True)
            self._layout.addWidget(desc_label)

        self._layout.addWidget(self._divider())

        # Episode counter
        counter = QLabel(f"Episode  {current}  /  {total}")
        counter.setStyleSheet(
            "color: #dddddd; font-size: 13px; font-weight: bold;"
        )
        self._layout.addWidget(counter)

        # Episode label
        ep_label = QLabel(episode.label)
        ep_label.setStyleSheet("color: #cccccc; font-size: 12px;")
        ep_label.setWordWrap(True)
        self._layout.addWidget(ep_label)

        self._layout.addWidget(self._divider())

        # Objects heading
        obj_heading = QLabel("Objects")
        obj_heading.setStyleSheet(
            "color: #888888; font-size: 11px; font-weight: bold; text-transform: uppercase;"
        )
        self._layout.addWidget(obj_heading)

        for obj in episode.objects:
            type_cfg = task.object_types.get(obj.type)
            color = type_cfg.color if type_cfg else "#888888"
            row = QWidget()
            row.setStyleSheet("background: transparent;")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 2, 0, 2)
            row_layout.setSpacing(8)

            # Colored icon
            icon_label = QLabel()
            icon_label.setPixmap(_color_icon(color, 12))
            icon_label.setFixedSize(12, 12)
            row_layout.addWidget(icon_label, 0, Qt.AlignVCenter)

            # Object label
            name_label = QLabel(obj.label)
            name_label.setStyleSheet("color: #ffffff; font-size: 12px;")
            row_layout.addWidget(name_label, 0, Qt.AlignVCenter)

            # Separator arrow
            arrow = QLabel("→")
            arrow.setStyleSheet("color: #666666; font-size: 12px;")
            row_layout.addWidget(arrow, 0, Qt.AlignVCenter)

            # Description
            desc = QLabel(obj.description or f"x={obj.x_cm:.1f}cm, y={obj.y_cm:.1f}cm, {obj.rotation_deg:.0f}°")
            desc.setStyleSheet("color: #aaaaaa; font-size: 12px;")
            desc.setWordWrap(True)
            row_layout.addWidget(desc, 1, Qt.AlignVCenter)

            self._layout.addWidget(row)

        # Pre-episode notes
        if episode.notes:
            self._layout.addWidget(self._divider())
            notes_heading = QLabel("Notes")
            notes_heading.setStyleSheet(
                "color: #888888; font-size: 11px; font-weight: bold;"
            )
            self._layout.addWidget(notes_heading)
            notes_text = QLabel(episode.notes)
            notes_text.setStyleSheet(
                "color: #ffcc44; font-size: 11px; background: #2a2400; "
                "padding: 6px; border-radius: 4px;"
            )
            notes_text.setWordWrap(True)
            self._layout.addWidget(notes_text)

        self._layout.addStretch()

    @staticmethod
    def _divider() -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("color: #333333;")
        return line
