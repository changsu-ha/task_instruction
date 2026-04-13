#!/usr/bin/env python3
"""Entry point for Robot Scenario Viewer.

Usage:
    python run.py
    python run.py --task tasks/pick_and_place.yaml
    python run.py --task tasks/shelf_sorting.yaml --log-dir /path/to/logs
"""
import argparse
import sys
from pathlib import Path

from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtWidgets import QApplication

# Make sure the repo root is in sys.path regardless of working directory
_ROOT = Path(__file__).parent.resolve()
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.main_window import MainWindow


def _dark_palette() -> QPalette:
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#1e1e1e"))
    palette.setColor(QPalette.WindowText, QColor("#dddddd"))
    palette.setColor(QPalette.Base, QColor("#252525"))
    palette.setColor(QPalette.AlternateBase, QColor("#2a2a2a"))
    palette.setColor(QPalette.ToolTipBase, QColor("#333333"))
    palette.setColor(QPalette.ToolTipText, QColor("#dddddd"))
    palette.setColor(QPalette.Text, QColor("#dddddd"))
    palette.setColor(QPalette.Button, QColor("#3a3a3a"))
    palette.setColor(QPalette.ButtonText, QColor("#dddddd"))
    palette.setColor(QPalette.BrightText, QColor("#ffffff"))
    palette.setColor(QPalette.Highlight, QColor("#3b7fbf"))
    palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    return palette


def main():
    parser = argparse.ArgumentParser(description="Robot Scenario Viewer")
    parser.add_argument(
        "--task",
        type=Path,
        default=None,
        help="Path to task YAML file (e.g. tasks/pick_and_place.yaml)",
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=_ROOT / "logs",
        help="Directory for session log files (default: ./logs)",
    )
    args = parser.parse_args()

    app = QApplication(sys.argv)
    app.setApplicationName("Robot Scenario Viewer")
    app.setStyle("Fusion")
    app.setPalette(_dark_palette())

    # Resolve task path relative to repo root if not absolute
    task_yaml: Path | None = None
    if args.task:
        task_yaml = args.task if args.task.is_absolute() else _ROOT / args.task
        if not task_yaml.exists():
            print(f"[ERROR] Task file not found: {task_yaml}", file=sys.stderr)
            sys.exit(1)

    window = MainWindow(task_yaml=task_yaml, log_dir=args.log_dir)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
