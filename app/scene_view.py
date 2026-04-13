from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsView

from core.episode_manager import EpisodeManager
from core.models import Episode, TaskConfig
from core.renderer import SceneRenderer


class SceneCanvas(QGraphicsView):
    """2D top-down workspace visualizer.

    Displays the robot base, objects, and target areas for the current episode.
    Supports Ctrl+scroll zoom and middle-mouse-drag pan.
    """

    def __init__(self, episode_manager: EpisodeManager, parent=None):
        super().__init__(parent)
        self._manager = episode_manager
        self._task_config: TaskConfig | None = None
        self._renderer: SceneRenderer | None = None

        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        self.setRenderHint(self.renderHints().value)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setBackgroundBrush(Qt.black)
        self.setStyleSheet("border: 1px solid #444;")

        episode_manager.episode_changed.connect(self._on_episode_changed)

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def load_task(self, task_config: TaskConfig):
        self._task_config = task_config
        self._renderer = SceneRenderer(task_config.workspace, px_per_cm=10.0)
        self._scene.setSceneRect(self._renderer.scene_rect())
        episode = self._manager.current_episode()
        if episode:
            self._redraw(episode)
        self.fitInView(self._scene.sceneRect(), Qt.KeepAspectRatio)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_episode_changed(self, episode: Episode, index: int):
        if self._renderer and self._task_config:
            self._redraw(episode)

    def _redraw(self, episode: Episode):
        self._scene.clear()
        items = self._renderer.render_episode(episode, self._task_config.object_types)
        for item in items:
            self._scene.addItem(item)

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
            self.scale(factor, factor)
        else:
            super().wheelEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._renderer:
            self.fitInView(self._scene.sceneRect(), Qt.KeepAspectRatio)
