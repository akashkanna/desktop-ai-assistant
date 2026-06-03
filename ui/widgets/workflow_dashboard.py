"""Workflow dashboard with stats, list, and editor."""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QLineEdit, QTextEdit, QTabWidget, QWidget, QSizePolicy,
)
from PySide6.QtCore import Signal, Qt, QSize

from ui.theme.theme_manager import Colors, ThemeManager
from ui.components.base import SectionHeader
from ui.layout.responsive import ResponsiveColumns
from ui.themes import glass_style


class StatChip(QFrame):
    def __init__(self, label: str, value: str = "0"):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background: rgba(10, 20, 40, 0.5);
                border: 1px solid {Colors.BORDER};
                border-radius: 12px;
            }}
        """)
        l = QVBoxLayout(self)
        l.setContentsMargins(12, 8, 12, 8)
        self._val = QLabel(value)
        self._val.setStyleSheet(f"color: {Colors.NEON_PURPLE}; font-size: 20px; font-weight: 900;")
        t = QLabel(label)
        t.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 9px; font-weight: 700;")
        l.addWidget(self._val)
        l.addWidget(t)

    def set_value(self, v: str):
        self._val.setText(v)


class WorkflowDashboard(QFrame):
    create_requested = Signal()
    save_requested = Signal(str, str, str)
    run_requested = Signal(str)
    delete_requested = Signal(str)
    voice_wizard_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"QFrame {{ {glass_style(16, True)} }}")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        header = QHBoxLayout()
        header.addWidget(SectionHeader("Workflow Dashboard", purple=True))
        header.addStretch()
        self.create_btn = QPushButton("+ Create")
        self.create_btn.setStyleSheet(ThemeManager.ghost_button())
        self.create_btn.clicked.connect(self.create_requested.emit)
        header.addWidget(self.create_btn)
        layout.addLayout(header)

        self.stat_total = StatChip("Total", "0")
        self.stat_active = StatChip("Active", "0")
        self.stat_runs = StatChip("Runs Today", "0")
        stats = ResponsiveColumns(
            [self.stat_total, self.stat_active, self.stat_runs],
            ratios=[1, 1, 1],
        )
        layout.addWidget(stats)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid {Colors.BORDER}; border-radius: 10px; background: rgba(10,20,40,0.4); }}
            QTabBar::tab {{ padding: 8px 16px; font-size: 11px; color: {Colors.TEXT_SECONDARY}; }}
            QTabBar::tab:selected {{ color: {Colors.NEON_PURPLE}; border-bottom: 2px solid {Colors.NEON_PURPLE}; }}
        """)
        self.tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tabs.setMinimumHeight(200)
        self.list_widget = QListWidget()
        self.list_widget.setMinimumHeight(120)
        self.list_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.list_widget.setStyleSheet(f"""
            QListWidget {{ background: transparent; border: none; font-size: 12px; }}
            QListWidget::item {{ padding: 12px 10px; margin: 4px 0; border-bottom: 1px solid {Colors.BORDER}; border-radius: 8px; }}
            QListWidget::item:selected {{ background: rgba(123, 97, 255, 0.16); color: {Colors.TEXT_PRIMARY}; }}
        """)
        self.tabs.addTab(self.list_widget, "Active")
        self.tabs.addTab(QWidget(), "History")
        self.tabs.addTab(QWidget(), "Favorites")
        layout.addWidget(self.tabs)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Workflow name")
        self.name_input.setMinimumHeight(34)
        self.name_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.trigger_input = QLineEdit()
        self.trigger_input.setPlaceholderText("Trigger phrase")
        self.trigger_input.setMinimumHeight(34)
        self.trigger_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        form_row = ResponsiveColumns([
            self.name_input,
            self.trigger_input,
        ], ratios=[1, 1])
        layout.addWidget(form_row)

        self.steps_input = QTextEdit()
        self.steps_input.setPlaceholderText("Steps (one per line)")
        self.steps_input.setMinimumHeight(110)
        self.steps_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.steps_input)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet(f"color: {Colors.WARNING}; font-size: 11px;")
        layout.addWidget(self.status_label)

        btn_row = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.run_btn = QPushButton("Run")
        self.delete_btn = QPushButton("Delete")
        self.voice_btn = QPushButton("Voice Builder")
        for btn in (self.save_btn, self.run_btn, self.delete_btn, self.voice_btn):
            btn.setStyleSheet(ThemeManager.ghost_button())
            btn.setMinimumHeight(32)
            btn_row.addWidget(btn)
        self.save_btn.clicked.connect(self._on_save)
        self.run_btn.clicked.connect(self._on_run)
        self.delete_btn.clicked.connect(self._on_delete)
        self.voice_btn.clicked.connect(self.voice_wizard_requested.emit)
        layout.addLayout(btn_row)

    def _on_save(self):
        self.save_requested.emit(
            self.name_input.text().strip(),
            self.trigger_input.text().strip(),
            self.steps_input.toPlainText().strip(),
        )

    def _on_run(self):
        item = self.list_widget.currentItem()
        name = item.text().split(" — ")[0].strip() if item else self.name_input.text().strip()
        if name:
            self.run_requested.emit(name)

    def _on_delete(self):
        item = self.list_widget.currentItem()
        name = item.text().split(" — ")[0].strip() if item else self.name_input.text().strip()
        if name:
            self.delete_requested.emit(name)

    def refresh_workflows(self, workflows: list):
        self.list_widget.clear()
        for wf in workflows:
            trigger = wf.get("trigger", "")
            label = f"{wf['name']} — trigger: {trigger}" if trigger else wf["name"]
            item = QListWidgetItem(label)
            item.setSizeHint(QSize(0, 40))
            self.list_widget.addItem(item)
        n = len(workflows)
        self.stat_total.set_value(str(n))
        self.stat_active.set_value(str(n))

    def load_workflow(self, workflow: dict):
        self.name_input.setText(workflow.get("name", ""))
        self.trigger_input.setText(workflow.get("trigger", ""))
        steps = workflow.get("steps", [])
        self.steps_input.setPlainText("\n".join(s.get("text", "") for s in steps if s.get("text")))

    def set_status(self, text: str, success: bool = False, error: bool = False):
        color = Colors.SUCCESS if success else Colors.DANGER if error else Colors.WARNING
        self.status_label.setStyleSheet(f"color: {color}; font-size: 11px;")
        self.status_label.setText(text)
