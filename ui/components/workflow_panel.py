"""Workflow management panel with CRUD controls."""

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QLineEdit, QTextEdit, QTabWidget, QWidget, QSizePolicy,
)
from PySide6.QtCore import Signal, Qt, QSize

from ui.theme.theme_manager import Colors, ThemeManager
from ui.components.base import GlassCard, SectionHeader
from ui.layout.responsive import ResponsiveToolbar


class WorkflowPanel(GlassCard):
    create_requested = Signal()
    save_requested = Signal(str, str, str)
    run_requested = Signal(str)
    delete_requested = Signal(str)
    voice_wizard_requested = Signal()

    def __init__(self):
        super().__init__(radius=16, glow=True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        self._header = ResponsiveToolbar()
        title = SectionHeader("Workflow Management", purple=True)
        self.create_btn = QPushButton("+ Create Workflow")
        self.create_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Colors.NEON_PURPLE};
                border: 1px solid {Colors.NEON_PURPLE};
                border-radius: 10px;
                padding: 6px 12px;
                font-weight: 700;
                font-size: 11px;
            }}
            QPushButton:hover {{ background: #7B61FF22; }}
        """)
        self.create_btn.clicked.connect(self.create_requested.emit)
        self._header.set_widgets(title, [self.create_btn])
        layout.addWidget(self._header)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {Colors.BORDER};
                border-radius: 10px;
                background: {Colors.BG_INPUT};
            }}
            QTabBar::tab {{
                background: {Colors.BG_CARD};
                color: {Colors.TEXT_SECONDARY};
                padding: 6px 12px;
                font-size: 11px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                color: {Colors.NEON_PURPLE};
                border-bottom: 2px solid {Colors.NEON_PURPLE};
            }}
        """)
        self.list_widget = QListWidget()
        self.list_widget.setMinimumHeight(80)
        self.list_widget.setMaximumHeight(140)
        self.list_widget.setStyleSheet(f"""
            QListWidget {{
                background: transparent;
                border: none;
                color: {Colors.TEXT_PRIMARY};
                font-size: 12px;
            }}
            QListWidget::item {{
                padding: 10px 8px;
                margin: 3px 0;
                border-bottom: 1px solid {Colors.BORDER};
                min-height: 28px;
            }}
            QListWidget::item:selected {{
                background: #7B61FF22;
                border-radius: 6px;
            }}
        """)
        self.tabs.addTab(self.list_widget, "All Workflows")
        self.tabs.addTab(QWidget(), "Active")
        self.tabs.addTab(QWidget(), "Favorites")
        layout.addWidget(self.tabs)

        form_label = QLabel("Editor")
        form_label.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 10px; font-weight: 700;")
        layout.addWidget(form_label)

        row = QHBoxLayout()
        row.setSpacing(8)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Workflow name")
        self.trigger_input = QLineEdit()
        self.trigger_input.setPlaceholderText("Trigger phrase")
        row.addWidget(self.name_input)
        row.addWidget(self.trigger_input)
        layout.addLayout(row)

        self.steps_input = QTextEdit()
        self.steps_input.setPlaceholderText("Steps (one action per line)")
        self.steps_input.setMinimumHeight(64)
        self.steps_input.setMaximumHeight(96)
        layout.addWidget(self.steps_input)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet(f"color: {Colors.WARNING}; font-size: 11px;")
        layout.addWidget(self.status_label)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        self.save_btn = QPushButton("Save")
        self.run_btn = QPushButton("Run")
        self.delete_btn = QPushButton("Delete")
        self.voice_btn = QPushButton("Voice Wizard")
        for btn in (self.save_btn, self.run_btn, self.delete_btn, self.voice_btn):
            btn.setStyleSheet(ThemeManager.ghost_button())
            btn.setMinimumHeight(32)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
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
            item.setSizeHint(QSize(0, 42))
            self.list_widget.addItem(item)

    def load_workflow(self, workflow: dict):
        self.name_input.setText(workflow.get("name", ""))
        self.trigger_input.setText(workflow.get("trigger", ""))
        steps = workflow.get("steps", [])
        self.steps_input.setPlainText("\n".join(s.get("text", "") for s in steps if s.get("text")))

    def set_status(self, text: str, success: bool = False, error: bool = False):
        color = Colors.SUCCESS if success else Colors.DANGER if error else Colors.WARNING
        self.status_label.setStyleSheet(f"color: {color}; font-size: 11px;")
        self.status_label.setText(text)
