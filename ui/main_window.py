"""
Jarvis AI OS — Premium futuristic desktop dashboard.
Hero-centric AI control center wired to AssistantController.
"""

import json
import threading
from pathlib import Path

from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QSplitter, QStackedWidget, QVBoxLayout, QDialog,
    QLineEdit, QTextEdit, QLabel, QPushButton, QSizePolicy,
)
from PySide6.QtCore import Signal, Slot, QTimer, Qt

from core.assistant_controller import AssistantController
from ui.components.base import FramelessWindow
from ui.components.header import HeaderBar
from ui.widgets import CollapsibleSidebar, CommandDock
from ui.pages.dashboard_page import DashboardPage
from ui.pages.placeholder_page import PlaceholderPage, ChatLogPanel
from ui.theme.theme_manager import ThemeManager, Colors
from services.system_monitor_service import SystemMonitorService
from services.activity_log_service import ActivityLogService
from services.integration_hooks import IntegrationRegistry
import automation.system_controls as sys_ctrl


class WorkflowDialog(QDialog):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setWindowTitle("Create Workflow")
        self.setMinimumSize(420, 380)
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.setStyleSheet(ThemeManager.global_stylesheet())
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        layout.addWidget(QLabel("Create a new workflow"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Workflow name")
        self.name_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.name_input)
        self.definition_input = QTextEdit()
        self.definition_input.setPlaceholderText("Steps (one per line)")
        self.definition_input.setMinimumHeight(140)
        self.definition_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.definition_input)
        self.message_label = QLabel("")
        self.message_label.setStyleSheet(f"color: {Colors.DANGER};")
        layout.addWidget(self.message_label)
        row = QHBoxLayout()
        cancel = QPushButton("Cancel")
        cancel.setStyleSheet(ThemeManager.ghost_button())
        cancel.clicked.connect(self.reject)
        save = QPushButton("Save Workflow")
        save.setStyleSheet(ThemeManager.gradient_button())
        save.clicked.connect(self._on_save)
        row.addWidget(cancel)
        row.addWidget(save)
        layout.addLayout(row)

    def _on_save(self):
        name = self.name_input.text().strip()
        steps_raw = self.definition_input.toPlainText().strip()
        if not name or not steps_raw:
            self.message_label.setText("Name and steps are required.")
            return
        steps = [{"text": s.strip()} for s in steps_raw.splitlines() if s.strip()]
        self.controller.workflow_engine.create_workflow(name, steps, trigger=name)
        self.accept()


class MainWindow(FramelessWindow):
    sig_status = Signal(str)
    sig_user_text = Signal(str)
    sig_jarvis_text = Signal(str)
    sig_mute = Signal(bool)
    sig_avatar = Signal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Jarvis AI — Desktop Assistant OS")
        self.resize(1366, 768)
        self.setMinimumSize(960, 620)

        self._settings = self._load_settings()
        self._integrations = IntegrationRegistry()
        self._activity = ActivityLogService(self)
        self._monitor = SystemMonitorService(self)
        self._gesture_enabled = False
        self._camera_enabled = False

        self.sig_status.connect(self._on_status)
        self.sig_user_text.connect(self._on_user_text)
        self.sig_jarvis_text.connect(self._on_jarvis_text)
        self.sig_mute.connect(self._on_mute)
        self.sig_avatar.connect(self._on_avatar_state)

        self._build_ui()
        self._wire_events()

        self.controller = AssistantController(ui_callback=self._controller_cb)
        self.controller.mic_monitor.levels_updated.connect(self._on_mic_levels)
        self.controller.mic_monitor.status_updated.connect(self._on_mic_status)
        self._apply_settings_to_ui()
        self._refresh_workflows()
        self._monitor.start()
        self._activity.log("Jarvis AI OS initialized", "system", "🚀")

        QTimer.singleShot(900, self._auto_start)

    def _load_settings(self) -> dict:
        path = Path(__file__).parent.parent / "config" / "settings.json"
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _build_ui(self):
        self.bg = QFrame()
        self.bg.setObjectName("RootFrame")
        self.bg.setStyleSheet(ThemeManager.global_stylesheet())
        self.setCentralWidget(self.bg)

        root = QHBoxLayout(self.bg)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.sidebar = CollapsibleSidebar()
        self.sidebar.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(10)
        splitter.setChildrenCollapsible(False)
        splitter.setContentsMargins(0, 0, 0, 0)
        splitter.addWidget(self.sidebar)
        splitter.setStyleSheet("QSplitter::handle { background: rgba(255,255,255,0.07); }")

        content_wrap = QFrame()
        content_wrap.setStyleSheet(f"background: {Colors.BG_PRIMARY};")
        content_wrap.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        content_layout = QVBoxLayout(content_wrap)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.header = HeaderBar()
        content_layout.addWidget(self.header)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent;")
        self.dashboard = DashboardPage(self._integrations)
        self.stack.addWidget(self.dashboard)

        self._pages: dict[str, int] = {"dashboard": 0}
        for key in (
            "voice", "gesture", "workflow", "apps", "system",
            "files", "screenshots", "memory", "logs", "settings", "help",
        ):
            page = PlaceholderPage(key)
            if key == "voice":
                self._voice_chat = ChatLogPanel()
                page.add_widget(self._voice_chat)
            self._pages[key] = self.stack.addWidget(page)

        content_layout.addWidget(self.stack, stretch=1)

        self.command_dock = CommandDock()
        content_layout.addWidget(self.command_dock)
        self.bottom_bar = self.command_dock  # backward compat alias

        splitter.addWidget(content_wrap)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        root.addWidget(splitter)

    def _wire_events(self):
        self.sidebar.page_selected.connect(self._navigate)

        # --- Window control buttons (delegate to FramelessWindow base) ---
        self.header.minimize_clicked.connect(self.minimize)
        self.header.maximize_clicked.connect(self.toggle_maximize)
        self.header.close_clicked.connect(self.close)
        self.header.search_submitted.connect(self._handle_search)

        # Keep the maximize/restore icon in sync with actual window state.
        self.window_state_changed.connect(self.header.update_maximize_icon)
        self.window_state_changed.connect(self._refresh_layout_on_state_change)

        dock = self.command_dock
        dock.listen_toggled.connect(self._toggle_listen)
        dock.mute_toggled.connect(self._toggle_mute)
        dock.gesture_toggled.connect(self._toggle_gesture_mode)
        dock.camera_toggled.connect(self._toggle_camera)
        dock.emergency_stop.connect(self._emergency_stop)
        dock.chat_submitted.connect(self._send_text)

        wf = self.dashboard.workflow
        wf.create_requested.connect(self._open_workflow_dialog)
        wf.save_requested.connect(self._save_workflow)
        wf.run_requested.connect(lambda n: self._run_workflow(n))
        wf.delete_requested.connect(self._delete_workflow)
        wf.voice_wizard_requested.connect(self._start_workflow_voice_wizard)
        wf.list_widget.itemSelectionChanged.connect(self._load_workflow_selection)

        self.dashboard.quick_actions.action_triggered.connect(self._handle_quick_action)
        self._monitor.metrics_updated.connect(self._on_metrics)
        self._activity.entry_added.connect(self.dashboard.activity.add_entry)

    def _refresh_layout_on_state_change(self, state: str):
        if state in ("normal", "maximized"):
            if self.centralWidget() is not None:
                cw = self.centralWidget()
                if cw.layout() is not None:
                    cw.layout().invalidate()
                cw.updateGeometry()
                cw.update()
            self.sidebar.updateGeometry()
            self.header.updateGeometry()
            self.stack.updateGeometry()
            self.stack.currentWidget().updateGeometry()
            self.dashboard.updateGeometry()
            self.repaint()

    def _on_metrics(self, metrics):
        self.dashboard.system_monitor.update_metrics(metrics)
        self.dashboard.ai_status.set_health(int(metrics.assistant_health))

    @Slot(list, float, float, float)
    def _on_mic_levels(self, levels, rms, peak, level_pct):
        self.dashboard.hero.waveform.set_levels(levels, level_pct)
        self.command_dock.waveform.set_levels(levels, level_pct)
        if self.controller.is_listening:
            self.command_dock.set_status(f"Listening… {int(level_pct)}%")

    @Slot(str)
    def _on_mic_status(self, status: str):
        self.dashboard.hero.set_voice_status(status)
        if not self.controller.is_listening:
            self.command_dock.set_status(status)

    def _apply_settings_to_ui(self):
        assistant = self._settings.get("assistant", {})
        wake_words = assistant.get("wake_words", ["hey assistant", "jarvis"])
        wake_display = ", ".join(wake_words[:2]).title()
        model = self._integrations.primary_model_label()
        self.dashboard.hero.set_wake_words(wake_display)
        self.dashboard.hero.set_model(model)
        self.dashboard.hero.set_memory_status("JSON Store Active")
        self.dashboard.hero.set_voice_status("Google STT Active")
        self.dashboard.ai_status.refresh()

        ui_cfg = self._settings.get("ui", {})
        self.resize(ui_cfg.get("window_width", 1440), ui_cfg.get("window_height", 920))

    def _navigate(self, key: str):
        idx = self._pages.get(key, 0)
        self.stack.setCurrentIndex(idx)

    def _controller_cb(self, **kwargs):
        if kwargs.get("status") is not None:
            self.sig_status.emit(kwargs["status"])
        if kwargs.get("user_text") is not None:
            self.sig_user_text.emit(kwargs["user_text"])
        if kwargs.get("assistant_text") is not None:
            self.sig_jarvis_text.emit(kwargs["assistant_text"])
        if kwargs.get("is_muted") is not None:
            self.sig_mute.emit(kwargs["is_muted"])
        if kwargs.get("avatar_state") is not None:
            self.sig_avatar.emit(kwargs["avatar_state"])

    @Slot(str)
    def _on_status(self, status: str):
        st = status.lower()
        self.command_dock.set_status(status)

        if "listen" in st:
            self.dashboard.hero.set_state("listening")
            self.command_dock.set_listening(True)
            self.header.set_status("Listening", Colors.NEON_BLUE)
            self.sidebar.set_assistant_status(True, "Listening")
        elif "think" in st or "execut" in st:
            self.dashboard.hero.set_state("thinking")
            self.header.set_status("Processing", Colors.NEON_YELLOW)
        elif "speak" in st:
            self.dashboard.hero.set_state("speaking")
            self.header.set_status("Speaking", Colors.NEON_PURPLE)
        else:
            self.dashboard.hero.set_state("idle")
            self.command_dock.set_listening(False)
            self.header.set_status("Connected", Colors.SUCCESS)
            self.sidebar.set_assistant_status(True, "Online")

    @Slot(str)
    def _on_user_text(self, text: str):
        if hasattr(self, "_voice_chat"):
            self._voice_chat.add_message(text, is_user=True)
        self._activity.log(text, "voice", "🎙")

    @Slot(str)
    def _on_jarvis_text(self, text: str):
        if hasattr(self, "_voice_chat"):
            self._voice_chat.add_message(text, is_user=False)
        self._activity.log(text, "ai", "🤖")

    @Slot(bool)
    def _on_mute(self, is_muted: bool):
        self.command_dock.set_voice_muted(is_muted)
        self.dashboard.hero.set_voice_status("Muted" if is_muted else "Active")

    @Slot(str)
    def _on_avatar_state(self, state: str):
        self.dashboard.hero.set_state(state)

    def _send_text(self, text: str = ""):
        if not text:
            text = self.command_dock.chat_input.text().strip()
        if text:
            self.command_dock.chat_input.clear()
            self.controller.process_text_input(text)
            self._refresh_workflows()

    def _handle_search(self, query: str):
        if query:
            self._send_text(query)

    def _toggle_listen(self):
        if self.controller.is_listening:
            self.controller.stop_listening()
            self._activity.log("Voice listening stopped", "voice", "⏸")
        else:
            self.controller.start_listening()
            self._activity.log("Voice listening started", "voice", "▶")

    def _toggle_mute(self):
        self.controller.toggle_mute()

    def _toggle_gesture_mode(self):
        gesture = self.controller.gesture_controller
        if gesture.gesture_enabled:
            result = gesture.stop_gesture()
            self._gesture_enabled = False
        else:
            result = gesture.start_gesture()
            self._gesture_enabled = gesture.gesture_enabled
        self.command_dock.set_gesture_enabled(self._gesture_enabled)
        self.dashboard.hero.set_gesture_mode(self._gesture_enabled)
        self.dashboard.ai_status.set_gesture(self._gesture_enabled, "Active" if self._gesture_enabled else "Off")
        self._activity.log(
            result,
            "gesture", "✋",
        )

    def _toggle_camera(self):
        if self._camera_enabled:
            result = self.controller.gesture_controller.stop_camera()
            self._camera_enabled = False
        else:
            result = self.controller.gesture_controller.start_camera()
            self._camera_enabled = self.controller.gesture_controller.camera_enabled
        self.command_dock.set_camera_enabled(self._camera_enabled)
        self._activity.log(result, "gesture", "📷")

    def _emergency_stop(self):
        self.controller.stop_listening()
        if self.controller.gesture_controller.gesture_enabled:
            self.controller.gesture_controller.stop_gesture()
        if self.controller.gesture_controller.camera_enabled:
            self.controller.gesture_controller.stop_camera()
        self._gesture_enabled = False
        self._camera_enabled = False
        self.command_dock.set_gesture_enabled(False)
        self.command_dock.set_camera_enabled(False)
        self.dashboard.hero.set_gesture_mode(False)
        self._activity.log("Emergency stop — all inputs halted", "system", "⛔")

    def _handle_quick_action(self, action: str):
        actions = {
            "open_app": lambda: self._send_text("open application"),
            "screenshot": lambda: self._exec_system(sys_ctrl.take_screenshot, "Screenshot saved successfully"),
            "lock": lambda: self._exec_system(sys_ctrl.lock_screen, "System locked"),
            "shutdown": lambda: self._exec_system(sys_ctrl.shutdown_system, "Shutdown initiated"),
            "restart": lambda: self._exec_system(sys_ctrl.restart_system, "Restart initiated"),
            "vol_up": lambda: self._exec_system(
                lambda: sys_ctrl.set_volume(min(100, sys_ctrl.get_volume() + 10)), "Volume increased"),
            "vol_down": lambda: self._exec_system(
                lambda: sys_ctrl.set_volume(max(0, sys_ctrl.get_volume() - 10)), "Volume decreased"),
            "browser": lambda: self._send_text("open browser"),
        }
        fn = actions.get(action)
        if fn:
            fn()

    def _exec_system(self, fn, log_msg: str):
        try:
            fn()
            self._activity.log(log_msg, "system", "⚙")
        except Exception as exc:
            self._activity.log(str(exc), "system", "⚠")

    # NOTE: _toggle_maximize removed — window management is now centralised
    # in FramelessWindow.toggle_maximize() (see ui/components/base.py).

    def _auto_start(self):
        self.controller.update_ui(
            assistant_text="Hello! I am Jarvis. Your AI operating system is online.",
            avatar_state="idle",
        )
        self.controller.start_listening()

    def _open_workflow_dialog(self):
        if WorkflowDialog(self.controller, self).exec() == QDialog.Accepted:
            self._refresh_workflows()
            self._activity.log("Workflow created", "workflow", "⚡")

    def _refresh_workflows(self):
        self.dashboard.workflow.refresh_workflows(self.controller.workflow_engine.list_workflows())

    def _save_workflow(self, name, trigger, steps_raw):
        if not name or not steps_raw:
            self.dashboard.workflow.set_status("Name and steps required.", error=True)
            return
        steps = [{"text": s.strip()} for s in steps_raw.splitlines() if s.strip()]
        self.controller.workflow_engine.create_workflow(name, steps, trigger=trigger or name)
        self._refresh_workflows()
        self.dashboard.workflow.set_status(f"Workflow '{name}' saved.", success=True)
        self._activity.log(f"Saved workflow: {name}", "workflow", "💾")

    def _run_workflow(self, name):
        self.controller.process_text_input(f"run workflow {name}")
        self._activity.log(f"Morning routine executed: {name}" if name else "Workflow executed", "workflow", "▶")

    def _delete_workflow(self, name):
        if self.controller.workflow_engine.remove_workflow(name):
            self._refresh_workflows()
            self.dashboard.workflow.set_status(f"Deleted '{name}'.", success=True)
            self._activity.log(f"Deleted workflow: {name}", "workflow", "🗑")
        else:
            self.dashboard.workflow.set_status("Could not delete workflow.", error=True)

    def _load_workflow_selection(self):
        item = self.dashboard.workflow.list_widget.currentItem()
        if not item:
            return
        wf = self.controller.workflow_engine.get_workflow(item.text().split(" — ")[0].strip())
        if wf:
            self.dashboard.workflow.load_workflow(wf)

    def _start_workflow_voice_wizard(self):
        if self.controller.is_listening:
            self._activity.log("Stop listener before voice builder", "workflow", "⚠")
            return
        self.dashboard.workflow.voice_btn.setEnabled(False)
        threading.Thread(target=self._listen_for_workflow_phrase, daemon=True).start()

    def _listen_for_workflow_phrase(self):
        text = self.controller.stt.listen(timeout=10, phrase_time_limit=18)
        if text:
            QTimer.singleShot(0, lambda: self.controller.process_text_input(text))
            QTimer.singleShot(0, self._refresh_workflows)
        else:
            QTimer.singleShot(0, lambda: self._activity.log("Voice builder: no input", "workflow", "⚠"))
        QTimer.singleShot(0, lambda: self.dashboard.workflow.voice_btn.setEnabled(True))

    def closeEvent(self, event):
        self.controller.shutdown()
        self._monitor.stop()
        event.accept()
