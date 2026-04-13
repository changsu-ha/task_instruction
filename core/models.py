from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ObjectTypeConfig:
    shape: str                  # "rectangle" | "circle"
    color: str                  # CSS hex color string
    width_cm: float = 0.0
    height_cm: float = 0.0
    radius_cm: float = 0.0
    style: str = "solid"        # "solid" | "dashed"


@dataclass
class PlacedObject:
    id: str
    type: str                   # references ObjectTypeConfig key
    x_cm: float
    y_cm: float
    rotation_deg: float
    label: str
    description: str


@dataclass
class RobotConfig:
    base_x_cm: float = 0.0
    base_y_cm: float = -20.0
    base_radius_cm: float = 5.0


@dataclass
class WorkspaceConfig:
    width_cm: float
    height_cm: float
    origin: str                 # "center" | "top-left"
    robot: RobotConfig = field(default_factory=RobotConfig)


@dataclass
class Episode:
    id: int
    label: str
    objects: List[PlacedObject]
    notes: str = ""


@dataclass
class TaskConfig:
    name: str
    description: str
    version: str
    workspace: WorkspaceConfig
    object_types: Dict[str, ObjectTypeConfig]
    episodes: List[Episode]


@dataclass
class LogEntry:
    episode_id: int
    task_name: str
    status: str                         # "collected" | "skipped" | "retry" | "pending"
    start_time: str                     # ISO 8601
    session_id: str
    end_time: Optional[str] = None
    duration_seconds: Optional[float] = None
    operator_notes: str = ""
    config_snapshot: Optional[dict] = None
