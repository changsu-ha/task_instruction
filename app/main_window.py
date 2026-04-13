from __future__ import annotations
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAction, QFileDialog, QMainWindow, QMessageBox,
    QSplitter, QVBoxLayout, QWidget,
)

from app.config_panel import ConfigPanel
from app.log_panel import LogPanel
from app.nav_bar import NavBar
from app.scene_view import SceneCanvas
from core.episode_manager import EpisodeManager
from core.logger import SessionLogger


class MainWindow(QMainWindow):
    """Root window: wires all widgets together using a QSplitter layout."""

    def __init__(self, task_yaml: Path | None = None, log_dir: Path = Path("logs")):
        super().__init__()
        self.setWindowTitle("Robot Scenario Viewer")
        self.resize(1200, 700)

        # Core objects
        self._manager = EpisodeManager(self)
        self._logger: SessionLogger | None = None
        self._log_dir = log_dir

        # Widgets
        self._scene_canvas = SceneCanvas(self._manager, self)
        self._config_panel = ConfigPanel(self._manager, self)
        self._log_panel: LogPanel | None = None
        self._nav_bar = NavBar(self._manager, self)

        self._build_layout()
        self._build_menu()

        if task_yaml:
            self._load_task(task_yaml)

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build_layout(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_vbox = QVBoxLayout(central)
        main_vbox.setContentsMargins(0, 0, 0, 0)
        main_vbox.setSpacing(0)

        # Horizontal splitter: scene (left) | right panel
        h_splitter = QSplitter(Qt.Horizontal)
        h_splitter.setHandleWidth(4)
        h_splitter.setStyleSheet("QSplitter::handle { background: #333; }")

        h_splitter.addWidget(self._scene_canvas)

        # Right: config panel (top) + log panel placeholder (bottom)
        self._right_widget = QWidget()
        self._right_widget.setStyleSheet("background: #1e1e1e;")
        self._right_vbox = QVBoxLayout(self._right_widget)
        self._right_vbox.setContentsMargins(0, 0, 0, 0)
        self._right_vbox.setSpacing(0)
        self._right_vbox.addWidget(self._config_panel, 1)
        h_splitter.addWidget(self._right_widget)

        h_splitter.setSizes([720, 480])

        main_vbox.addWidget(h_splitter, 1)
        main_vbox.addWidget(self._nav_bar)

    # ------------------------------------------------------------------
    # Menu
    # ------------------------------------------------------------------

    def _build_menu(self):
        menubar = self.menuBar()
        menubar.setStyleSheet(
            "QMenuBar { background: #1e1e1e; color: #cccccc; }"
            "QMenuBar::item:selected { background: #333; }"
            "QMenu { background: #252525; color: #cccccc; }"
            "QMenu::item:selected { background: #3a3a3a; }"
        )

        file_menu = menubar.addMenu("File")

        open_action = QAction("Open Task…", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._on_open_task)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        export_action = QAction("Export Log…", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self._on_export)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        help_menu = menubar.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _load_task(self, yaml_path: Path):
        try:
            task_config = self._manager.load_task(yaml_path)
        except Exception as exc:
            QMessageBox.critical(self, "Load Error", f"Failed to load task:\n{exc}")
            return

        # Create logger for this task
        self._logger = SessionLogger(task_config.name, self._log_dir)

        # (Re)attach log panel
        if self._log_panel is not None:
            self._right_vbox.removeWidget(self._log_panel)
            self._log_panel.deleteLater()

        self._log_panel = LogPanel(self._manager, self._logger, self._right_widget)
        self._right_vbox.addWidget(self._log_panel)

        self._scene_canvas.load_task(task_config)
        self._config_panel.load_task(task_config)
        self._nav_bar.load_task()

        # Start timing episode 0
        self._log_panel.start_current_episode()

        self.setWindowTitle(f"Robot Scenario Viewer — {task_config.name}")
        self.statusBar().showMessage(
            f"Loaded: {yaml_path.name}  |  {task_config.name}  |  "
            f"{len(task_config.episodes)} episodes",
            5000,
        )

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_open_task(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Task YAML", str(Path("tasks")), "YAML (*.yaml *.yml)"
        )
        if path:
            self._load_task(Path(path))

    def _on_export(self):
        if self._log_panel:
            self._log_panel._on_export()
        else:
            QMessageBox.information(self, "No Data", "No task loaded yet.")

    def _on_about(self):
        QMessageBox.about(
            self,
            "About Robot Scenario Viewer",
            "<b>Robot Scenario Viewer</b><br><br>"
            "A lightweight tool for VLA robot manipulation data collection.<br>"
            "Shows episode configurations graphically and logs collection status.<br><br>"
            "Keyboard shortcuts:<br>"
            "  Ctrl+O — Open task<br>"
            "  Ctrl+E — Export log<br>"
            "  Ctrl+scroll — Zoom scene<br>"
            "  Drag — Pan scene",
        )
