"""Responsive layout helpers and breakpoint constants."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QSizePolicy, QLayout
from PySide6.QtCore import Qt


class Breakpoints:
    COMPACT = 900
    MEDIUM = 1200
    WIDE = 1400


def _clear_layout(layout: QLayout):
    while layout.count():
        item = layout.takeAt(0)
        if item.widget():
            layout.removeWidget(item.widget())
        elif item.layout():
            _clear_layout(item.layout())


class ResponsiveColumns(QWidget):
    """Stacks child column widgets horizontally, in a grid, or vertically based on width."""

    MIN_COL_WIDTH = 320

    def __init__(self, columns: list[QWidget], ratios: list[int] | None = None, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._columns = columns
        self._ratios = ratios or [1] * len(columns)
        self._h_layout = QHBoxLayout()
        self._grid_layout = QGridLayout()
        self._v_layout = QVBoxLayout()
        for layout in (self._h_layout, self._grid_layout, self._v_layout):
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(16)
        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(0, 0, 0, 0)
        self._mode = None
        self._apply_layout("horizontal")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        width = self.width()
        if width >= self.MIN_COL_WIDTH * len(self._columns):
            target = "horizontal"
        elif width >= self.MIN_COL_WIDTH * min(2, len(self._columns)):
            target = "grid"
        else:
            target = "vertical"
        if target != self._mode:
            self._apply_layout(target)

    def _apply_layout(self, mode: str):
        self._mode = mode
        _clear_layout(self._h_layout)
        _clear_layout(self._grid_layout)
        _clear_layout(self._v_layout)
        _clear_layout(self._outer)

        if mode == "horizontal":
            for col, ratio in zip(self._columns, self._ratios):
                col.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                col.setMinimumWidth(self.MIN_COL_WIDTH)
                self._h_layout.addWidget(col, ratio)
            self._outer.addLayout(self._h_layout)
        elif mode == "grid":
            columns = min(2, len(self._columns))
            for idx, col in enumerate(self._columns):
                col.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                col.setMinimumWidth(self.MIN_COL_WIDTH)
                self._grid_layout.addWidget(col, idx // columns, idx % columns)
            self._outer.addLayout(self._grid_layout)
        else:
            for col in self._columns:
                col.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                col.setMinimumWidth(0)
                self._v_layout.addWidget(col)
            self._outer.addLayout(self._v_layout)


class ResponsiveHeroLayout(QWidget):
    """Hero content that stacks on narrow widths."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._left = None
        self._center = None
        self._right = None
        self._h = QHBoxLayout()
        self._v = QVBoxLayout()
        self._h.setSpacing(20)
        self._h.setContentsMargins(0, 0, 0, 0)
        self._v.setSpacing(14)
        self._v.setContentsMargins(0, 0, 0, 0)
        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(0, 0, 0, 0)
        self._mode = None

    def set_sections(self, left: QWidget, center: QWidget, right: QWidget):
        self._left, self._center, self._right = left, center, right
        self._apply(compact=self.width() < 720)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        compact = self.width() < 720
        if compact != self._mode:
            self._apply(compact)

    def _apply(self, compact: bool):
        self._mode = compact
        _clear_layout(self._h)
        _clear_layout(self._v)
        _clear_layout(self._outer)
        if not self._left:
            return
        if compact:
            for w in (self._left, self._center, self._right):
                w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                self._v.addWidget(w, alignment=Qt.AlignHCenter)
            self._outer.addLayout(self._v)
        else:
            for w, stretch in ((self._left, 2), (self._center, 3), (self._right, 2)):
                w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                self._h.addWidget(w, stretch)
            self._outer.addLayout(self._h)


class ResponsiveToolbar(QWidget):
    """Title row that stacks when space is tight."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._title = None
        self._actions: list[QWidget] = []
        self._h = QHBoxLayout()
        self._v = QVBoxLayout()
        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(0, 0, 0, 0)
        self._mode = None

    def set_widgets(self, title: QWidget, actions: list[QWidget]):
        self._title = title
        self._actions = actions
        self._rebuild(self.width() < 420)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        stacked = self.width() < 420
        if stacked != self._mode:
            self._rebuild(stacked)

    def _rebuild(self, stacked: bool):
        self._mode = stacked
        _clear_layout(self._h)
        _clear_layout(self._v)
        _clear_layout(self._outer)
        if not self._title:
            return
        if stacked:
            self._v.addWidget(self._title)
            row = QHBoxLayout()
            for a in self._actions:
                row.addWidget(a)
            row.addStretch()
            self._v.addLayout(row)
            self._outer.addLayout(self._v)
        else:
            self._h.addWidget(self._title)
            self._h.addStretch()
            for a in self._actions:
                self._h.addWidget(a)
            self._outer.addLayout(self._h)
