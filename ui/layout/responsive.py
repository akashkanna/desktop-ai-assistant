"""Responsive layout helpers and breakpoint constants."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy
from PySide6.QtCore import Qt


class Breakpoints:
    COMPACT = 900
    MEDIUM = 1200
    WIDE = 1400


def _clear_layout(layout):
    while layout.count():
        item = layout.takeAt(0)
        w = item.widget()
        if w:
            layout.removeWidget(w)


class ResponsiveColumns(QWidget):
    """Stacks child column widgets horizontally or vertically based on width."""

    MIN_COL_WIDTH = 300

    def __init__(self, columns: list[QWidget], ratios: list[int] | None = None, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._columns = columns
        self._ratios = ratios or [1] * len(columns)
        self._h_layout = QHBoxLayout()
        self._v_layout = QVBoxLayout()
        self._h_layout.setContentsMargins(0, 0, 0, 0)
        self._h_layout.setSpacing(16)
        self._v_layout.setContentsMargins(0, 0, 0, 0)
        self._v_layout.setSpacing(16)
        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(0, 0, 0, 0)
        self._mode = None
        self._apply_layout(compact=True)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        needed = self.MIN_COL_WIDTH * len(self._columns) + 32
        compact = self.width() < needed
        if compact != self._mode:
            self._apply_layout(compact)

    def _apply_layout(self, compact: bool):
        self._mode = compact
        _clear_layout(self._h_layout)
        _clear_layout(self._v_layout)
        _clear_layout(self._outer)

        if compact:
            for col in self._columns:
                col.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                col.setMinimumWidth(0)
                self._v_layout.addWidget(col)
            self._outer.addLayout(self._v_layout)
        else:
            for col, ratio in zip(self._columns, self._ratios):
                col.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                col.setMinimumWidth(self.MIN_COL_WIDTH)
                self._h_layout.addWidget(col, ratio)
            self._outer.addLayout(self._h_layout)


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
