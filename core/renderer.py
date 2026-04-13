from __future__ import annotations
import math
from typing import Dict, List

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import (
    QBrush, QColor, QPen, QPolygonF, QTransform,
)
from PyQt5.QtWidgets import (
    QGraphicsEllipseItem, QGraphicsItem, QGraphicsLineItem,
    QGraphicsPolygonItem, QGraphicsRectItem, QGraphicsSimpleTextItem,
)

from core.models import Episode, ObjectTypeConfig, PlacedObject, WorkspaceConfig

# Grid line interval in cm
GRID_INTERVAL_CM = 10.0
# Extra padding around workspace (cm)
WORKSPACE_PADDING_CM = 5.0


class SceneRenderer:
    """Translates an Episode + TaskConfig into QGraphicsItems.

    Stateless with respect to episodes — call render_episode() each time
    the episode changes and replace all items in the QGraphicsScene.
    """

    def __init__(self, workspace: WorkspaceConfig, px_per_cm: float = 8.0):
        self.workspace = workspace
        self.px_per_cm = px_per_cm

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def scene_rect(self) -> QRectF:
        """Return the bounding rect of the workspace in scene coordinates."""
        w = self.workspace.width_cm + 2 * WORKSPACE_PADDING_CM
        h = self.workspace.height_cm + 2 * WORKSPACE_PADDING_CM
        return QRectF(0, 0, self.cm_to_px(w), self.cm_to_px(h))

    def render_episode(
        self,
        episode: Episode,
        object_types: Dict[str, ObjectTypeConfig],
    ) -> List[QGraphicsItem]:
        items: List[QGraphicsItem] = []
        items.extend(self._render_grid())
        items.extend(self._render_robot_base())
        for obj in episode.objects:
            type_cfg = object_types.get(obj.type)
            if type_cfg is None:
                continue
            items.extend(self._render_object(obj, type_cfg))
        return items

    # ------------------------------------------------------------------
    # Coordinate helpers
    # ------------------------------------------------------------------

    def cm_to_px(self, cm: float) -> float:
        return cm * self.px_per_cm

    def world_to_scene(self, x_cm: float, y_cm: float) -> QPointF:
        """Convert real-world (cm) coordinates to Qt scene pixel coordinates.

        Origin placement depends on workspace.origin:
          - "center": workspace center maps to scene center
          - "top-left": workspace top-left corner maps to scene (0,0)

        Qt Y-axis points downward; real-world Y points away from robot (upward
        on the top-down map), so we invert Y.
        """
        pad = WORKSPACE_PADDING_CM
        if self.workspace.origin == "center":
            scene_x = self.cm_to_px(x_cm + self.workspace.width_cm / 2 + pad)
            scene_y = self.cm_to_px(-y_cm + self.workspace.height_cm / 2 + pad)
        else:
            scene_x = self.cm_to_px(x_cm + pad)
            scene_y = self.cm_to_px(-y_cm + self.workspace.height_cm + pad)
        return QPointF(scene_x, scene_y)

    # ------------------------------------------------------------------
    # Grid
    # ------------------------------------------------------------------

    def _render_grid(self) -> List[QGraphicsItem]:
        items: List[QGraphicsItem] = []
        pen_minor = QPen(QColor("#2a2a2a"), 0.5, Qt.SolidLine)
        pen_major = QPen(QColor("#3a3a3a"), 1.0, Qt.SolidLine)
        pen_axis = QPen(QColor("#4a4a4a"), 1.5, Qt.SolidLine)

        rect = self.scene_rect()
        w_cm = self.workspace.width_cm + 2 * WORKSPACE_PADDING_CM
        h_cm = self.workspace.height_cm + 2 * WORKSPACE_PADDING_CM

        half_w = self.workspace.width_cm / 2 if self.workspace.origin == "center" else 0
        half_h = self.workspace.height_cm / 2 if self.workspace.origin == "center" else 0

        x_cm = -half_w - WORKSPACE_PADDING_CM
        while x_cm <= half_w + self.workspace.width_cm / 2 + WORKSPACE_PADDING_CM:
            sx = self.world_to_scene(x_cm, 0).x()
            if abs(x_cm) < 0.01:
                pen = pen_axis
            elif abs(x_cm % (GRID_INTERVAL_CM * 5)) < 0.01:
                pen = pen_major
            else:
                pen = pen_minor
            line = QGraphicsLineItem(sx, rect.top(), sx, rect.bottom())
            line.setPen(pen)
            line.setZValue(-10)
            items.append(line)
            x_cm += GRID_INTERVAL_CM

        y_cm = -half_h - WORKSPACE_PADDING_CM
        while y_cm <= half_h + self.workspace.height_cm / 2 + WORKSPACE_PADDING_CM:
            sy = self.world_to_scene(0, y_cm).y()
            if abs(y_cm) < 0.01:
                pen = pen_axis
            elif abs(y_cm % (GRID_INTERVAL_CM * 5)) < 0.01:
                pen = pen_major
            else:
                pen = pen_minor
            line = QGraphicsLineItem(rect.left(), sy, rect.right(), sy)
            line.setPen(pen)
            line.setZValue(-10)
            items.append(line)
            y_cm += GRID_INTERVAL_CM

        # Workspace boundary
        boundary_pen = QPen(QColor("#555555"), 1.5, Qt.DashLine)
        origin = self.world_to_scene(
            -half_w, half_h + (self.workspace.height_cm if self.workspace.origin != "center" else 0)
        )
        bw = self.cm_to_px(self.workspace.width_cm)
        bh = self.cm_to_px(self.workspace.height_cm)
        if self.workspace.origin == "center":
            bx = self.world_to_scene(-self.workspace.width_cm / 2, self.workspace.height_cm / 2).x()
            by = self.world_to_scene(0, self.workspace.height_cm / 2).y()
        else:
            bx = self.world_to_scene(0, self.workspace.height_cm).x()
            by = self.world_to_scene(0, self.workspace.height_cm).y()
        boundary = QGraphicsRectItem(bx, by, bw, bh)
        boundary.setPen(boundary_pen)
        boundary.setBrush(QBrush(Qt.NoBrush))
        boundary.setZValue(-9)
        items.append(boundary)

        return items

    # ------------------------------------------------------------------
    # Robot base
    # ------------------------------------------------------------------

    def _render_robot_base(self) -> List[QGraphicsItem]:
        items: List[QGraphicsItem] = []
        ws = self.workspace
        r_cm = ws.robot.base_radius_cm
        cx, cy = ws.robot.base_x_cm, ws.robot.base_y_cm
        center = self.world_to_scene(cx, cy)
        r_px = self.cm_to_px(r_cm)

        # Outer circle
        pen = QPen(QColor("#aaaaaa"), 2)
        brush = QBrush(QColor("#333333"))
        ellipse = QGraphicsEllipseItem(
            center.x() - r_px, center.y() - r_px, r_px * 2, r_px * 2
        )
        ellipse.setPen(pen)
        ellipse.setBrush(brush)
        ellipse.setZValue(1)
        items.append(ellipse)

        # Inner dot
        dot_r = r_px * 0.3
        dot = QGraphicsEllipseItem(
            center.x() - dot_r, center.y() - dot_r, dot_r * 2, dot_r * 2
        )
        dot.setPen(QPen(Qt.NoPen))
        dot.setBrush(QBrush(QColor("#aaaaaa")))
        dot.setZValue(2)
        items.append(dot)

        # Label
        label = QGraphicsSimpleTextItem("Robot")
        label.setBrush(QBrush(QColor("#aaaaaa")))
        label.setPos(center.x() - label.boundingRect().width() / 2,
                     center.y() + r_px + 2)
        label.setZValue(2)
        items.append(label)

        return items

    # ------------------------------------------------------------------
    # Objects
    # ------------------------------------------------------------------

    def _render_object(
        self, obj: PlacedObject, type_cfg: ObjectTypeConfig
    ) -> List[QGraphicsItem]:
        items: List[QGraphicsItem] = []
        center = self.world_to_scene(obj.x_cm, obj.y_cm)
        color = QColor(type_cfg.color)
        alpha_color = QColor(type_cfg.color)
        alpha_color.setAlpha(160)

        pen_style = Qt.DashLine if type_cfg.style == "dashed" else Qt.SolidLine
        pen = QPen(color, 2, pen_style)
        brush = QBrush(alpha_color)

        shape_item: QGraphicsItem

        if type_cfg.shape == "rectangle":
            w_px = self.cm_to_px(type_cfg.width_cm)
            h_px = self.cm_to_px(type_cfg.height_cm)
            rect_item = QGraphicsRectItem(-w_px / 2, -h_px / 2, w_px, h_px)
            rect_item.setPen(pen)
            rect_item.setBrush(brush)
            rect_item.setPos(center)
            rect_item.setRotation(-obj.rotation_deg)   # Qt rotation is CW; negate for math convention
            rect_item.setZValue(3)
            items.append(rect_item)
            shape_item = rect_item
        else:
            r_px = self.cm_to_px(type_cfg.radius_cm if type_cfg.radius_cm > 0 else 3.0)
            ell = QGraphicsEllipseItem(-r_px, -r_px, r_px * 2, r_px * 2)
            ell.setPen(pen)
            ell.setBrush(brush)
            ell.setPos(center)
            ell.setZValue(3)
            items.append(ell)
            shape_item = ell

        # Orientation arrow (only if not a target area with dashed style)
        if obj.rotation_deg != 0 or type_cfg.style != "dashed":
            arrow_items = self._render_orientation_arrow(
                center.x(), center.y(), obj.rotation_deg, type_cfg.color
            )
            items.extend(arrow_items)

        # Label
        text = QGraphicsSimpleTextItem(obj.label)
        text.setBrush(QBrush(QColor("#ffffff")))
        text_w = text.boundingRect().width()
        text.setPos(center.x() - text_w / 2, center.y() - 8)
        text.setZValue(5)
        items.append(text)

        return items

    def _render_orientation_arrow(
        self, cx: float, cy: float, rotation_deg: float, color_str: str
    ) -> List[QGraphicsItem]:
        """Draw a forward-direction arrow from (cx, cy)."""
        items: List[QGraphicsItem] = []
        arrow_color = QColor(color_str).darker(150)
        pen = QPen(arrow_color, 2)

        length_px = self.cm_to_px(4.0)
        angle_rad = math.radians(-rotation_deg + 90)   # +90 so 0° = pointing up
        dx = math.cos(angle_rad) * length_px
        dy = math.sin(angle_rad) * length_px

        # Shaft
        shaft = QGraphicsLineItem(cx, cy, cx + dx, cy - dy)
        shaft.setPen(pen)
        shaft.setZValue(4)
        items.append(shaft)

        # Arrowhead
        head_len = self.cm_to_px(1.5)
        head_angle = math.radians(30)
        tip_x = cx + dx
        tip_y = cy - dy
        left_x = tip_x - head_len * math.cos(angle_rad - head_angle)
        left_y = tip_y + head_len * math.sin(angle_rad - head_angle)
        right_x = tip_x - head_len * math.cos(angle_rad + head_angle)
        right_y = tip_y + head_len * math.sin(angle_rad + head_angle)

        head = QGraphicsPolygonItem(QPolygonF([
            QPointF(tip_x, tip_y),
            QPointF(left_x, left_y),
            QPointF(right_x, right_y),
        ]))
        head.setPen(QPen(Qt.NoPen))
        head.setBrush(QBrush(arrow_color))
        head.setZValue(4)
        items.append(head)

        return items
