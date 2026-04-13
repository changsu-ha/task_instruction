from __future__ import annotations
import random
from pathlib import Path
from typing import Optional

import yaml
from PyQt5.QtCore import QObject, pyqtSignal

from core.models import (
    Episode, ObjectTypeConfig, PlacedObject, RobotConfig,
    TaskConfig, WorkspaceConfig,
)


class EpisodeManager(QObject):
    """Loads a task YAML and manages navigation between episodes.

    Emits episode_changed(episode, index) whenever the current episode changes.
    index is 0-based.
    """

    episode_changed = pyqtSignal(object, int)   # (Episode, index)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._task: Optional[TaskConfig] = None
        self._current_index: int = 0

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load_task(self, yaml_path: Path) -> TaskConfig:
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        self._task = self._parse_task(data)
        self._current_index = 0
        return self._task

    def _parse_task(self, data: dict) -> TaskConfig:
        task_data = data["task"]
        ws_data = task_data["workspace"]
        robot_data = task_data.get("robot", {})

        robot = RobotConfig(
            base_x_cm=float(robot_data.get("base_x_cm", 0.0)),
            base_y_cm=float(robot_data.get("base_y_cm", -20.0)),
            base_radius_cm=float(robot_data.get("base_radius_cm", 5.0)),
        )
        workspace = WorkspaceConfig(
            width_cm=float(ws_data["width_cm"]),
            height_cm=float(ws_data["height_cm"]),
            origin=ws_data.get("origin", "center"),
            robot=robot,
        )

        object_types: dict = {}
        for name, cfg in task_data.get("object_types", {}).items():
            object_types[name] = ObjectTypeConfig(
                shape=cfg.get("shape", "rectangle"),
                color=cfg.get("color", "#888888"),
                width_cm=float(cfg.get("width_cm", 0.0)),
                height_cm=float(cfg.get("height_cm", 0.0)),
                radius_cm=float(cfg.get("radius_cm", 0.0)),
                style=cfg.get("style", "solid"),
            )

        episodes: list = []
        for ep_data in data.get("episodes", []):
            objects = []
            for obj in ep_data.get("objects", []):
                objects.append(PlacedObject(
                    id=str(obj["id"]),
                    type=str(obj["type"]),
                    x_cm=float(obj.get("x_cm", 0.0)),
                    y_cm=float(obj.get("y_cm", 0.0)),
                    rotation_deg=float(obj.get("rotation_deg", 0.0)),
                    label=str(obj.get("label", obj["id"])),
                    description=str(obj.get("description", "")),
                ))
            episodes.append(Episode(
                id=int(ep_data["id"]),
                label=str(ep_data.get("label", f"Episode {ep_data['id']}")),
                objects=objects,
                notes=str(ep_data.get("notes", "")),
            ))

        return TaskConfig(
            name=task_data["name"],
            description=task_data.get("description", ""),
            version=str(task_data.get("version", "1.0")),
            workspace=workspace,
            object_types=object_types,
            episodes=episodes,
        )

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    @property
    def task(self) -> Optional[TaskConfig]:
        return self._task

    def current_episode(self) -> Optional[Episode]:
        if self._task is None or not self._task.episodes:
            return None
        return self._task.episodes[self._current_index]

    def current_index(self) -> int:
        return self._current_index

    def total(self) -> int:
        return len(self._task.episodes) if self._task else 0

    def go_to(self, index: int):
        if self._task is None:
            return
        index = max(0, min(index, len(self._task.episodes) - 1))
        self._current_index = index
        self.episode_changed.emit(self.current_episode(), self._current_index)

    def next(self):
        if self._task is None:
            return
        new_index = (self._current_index + 1) % len(self._task.episodes)
        self.go_to(new_index)

    def prev(self):
        if self._task is None:
            return
        new_index = (self._current_index - 1) % len(self._task.episodes)
        self.go_to(new_index)

    def random(self):
        if self._task is None or len(self._task.episodes) <= 1:
            return
        candidates = [i for i in range(len(self._task.episodes)) if i != self._current_index]
        self.go_to(random.choice(candidates))
