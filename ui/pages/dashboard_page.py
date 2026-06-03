"""Dashboard — hero-centric AI control center layout."""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QScrollArea, QWidget, QSizePolicy
from PySide6.QtCore import Qt

from ui.widgets.ai_core_hero import AiCoreHero
from ui.widgets.ai_core_status import AiCoreStatusPanel
from ui.widgets.quick_actions_grid import QuickActionsGrid
from ui.widgets.workflow_dashboard import WorkflowDashboard
from ui.widgets.activity_timeline import ActivityTimeline
from ui.widgets.system_monitor_bars import SystemMonitorBars
from ui.layout.responsive import ResponsiveColumns
from services.integration_hooks import IntegrationRegistry


class DashboardPage(QScrollArea):
    def __init__(self, registry: IntegrationRegistry | None = None):
        super().__init__()
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        root = QVBoxLayout(container)
        root.setContentsMargins(14, 12, 14, 12)
        root.setSpacing(12)

        # ── HERO BAND: AI Core + Status Panel ──
        hero_band = QHBoxLayout()
        hero_band.setSpacing(12)
        self.hero = AiCoreHero()
        self.ai_status = AiCoreStatusPanel(registry)
        hero_band.addWidget(self.hero, stretch=5)
        hero_band.addWidget(self.ai_status, stretch=2)
        root.addLayout(hero_band)

        # ── MIDDLE: 3-column dashboard ──
        self.quick_actions = QuickActionsGrid()
        self.workflow = WorkflowDashboard()
        self.activity = ActivityTimeline()

        self._col1 = QWidget()
        l1 = QVBoxLayout(self._col1)
        l1.setContentsMargins(0, 0, 0, 0)
        l1.addWidget(self.quick_actions)

        self._col2 = QWidget()
        l2 = QVBoxLayout(self._col2)
        l2.setContentsMargins(0, 0, 0, 0)
        l2.addWidget(self.workflow)

        self._col3 = QWidget()
        l3 = QVBoxLayout(self._col3)
        l3.setContentsMargins(0, 0, 0, 0)
        l3.addWidget(self.activity)

        self._columns = ResponsiveColumns(
            [self._col1, self._col2, self._col3],
            ratios=[2, 3, 2],
        )
        self._columns.setMinimumHeight(280)
        root.addWidget(self._columns, stretch=1)

        # ── SYSTEM MONITOR (full width bars) ──
        self.system_monitor = SystemMonitorBars()
        root.addWidget(self.system_monitor)

        self.setWidget(container)
