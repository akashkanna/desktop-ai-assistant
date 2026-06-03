"""Reusable Qt animation helpers."""

from PySide6.QtCore import (
    QPropertyAnimation,
    QEasingCurve,
    QParallelAnimationGroup,
    QAbstractAnimation,
)
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QWidget
from PySide6.QtGui import QColor


def apply_glow(
    widget: QWidget,
    color: str = "#00A3FF",
    blur: int = 28,
    offset=(0, 0),
    alpha: int = 160,
) -> QGraphicsDropShadowEffect:
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    qc = QColor(color)
    qc.setAlpha(alpha)
    effect.setColor(qc)
    effect.setOffset(*offset)
    widget.setGraphicsEffect(effect)
    return effect


def fade_in(widget: QWidget, duration: int = 350) -> QPropertyAnimation:
    opacity = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(opacity)
    anim = QPropertyAnimation(opacity, b"opacity", widget)
    anim.setDuration(duration)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.OutCubic)
    anim.start(QAbstractAnimation.DeleteWhenStopped)
    return anim


def pulse_opacity(widget: QWidget, duration: int = 1200) -> QPropertyAnimation:
    effect = widget.graphicsEffect()
    if not isinstance(effect, QGraphicsOpacityEffect):
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
    anim = QPropertyAnimation(effect, b"opacity", widget)
    anim.setDuration(duration)
    anim.setStartValue(0.55)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.InOutSine)
    anim.setLoopCount(-1)
    anim.start()
    widget._pulse_anim = anim  # prevent GC
    return anim


def hover_scale_effect(widget: QWidget) -> None:
    """Store original geometry on enter/leave for subtle hover feedback."""
    widget.setProperty("_hover_base", widget.size())
    widget.installEventFilter(_HoverScaleFilter(widget))


class _HoverScaleFilter:
    def __init__(self, widget: QWidget):
        self.widget = widget

    def eventFilter(self, obj, event):
        from PySide6.QtCore import QEvent
        if obj is not self.widget:
            return False
        if event.type() == QEvent.Enter:
            anim = QPropertyAnimation(self.widget, b"maximumHeight", self.widget)
            anim.setDuration(180)
            anim.setStartValue(self.widget.height())
            anim.setEndValue(self.widget.height() + 2)
            anim.setEasingCurve(QEasingCurve.OutCubic)
            anim.start(QAbstractAnimation.DeleteWhenStopped)
        elif event.type() == QEvent.Leave:
            anim = QPropertyAnimation(self.widget, b"maximumHeight", self.widget)
            anim.setDuration(180)
            anim.setStartValue(self.widget.height())
            anim.setEndValue(max(1, self.widget.height() - 2))
            anim.setEasingCurve(QEasingCurve.OutCubic)
            anim.start(QAbstractAnimation.DeleteWhenStopped)
        return False


def crossfade_pages(old_page: QWidget, new_page: QWidget, stack, duration: int = 280):
    """Fade between stacked pages."""
    group = QParallelAnimationGroup(stack)

    old_op = QGraphicsOpacityEffect(old_page)
    old_page.setGraphicsEffect(old_op)
    fade_out = QPropertyAnimation(old_op, b"opacity", stack)
    fade_out.setDuration(duration)
    fade_out.setStartValue(1.0)
    fade_out.setEndValue(0.0)

    new_op = QGraphicsOpacityEffect(new_page)
    new_page.setGraphicsEffect(new_op)
    new_op.setOpacity(0.0)
    fade_in_anim = QPropertyAnimation(new_op, b"opacity", stack)
    fade_in_anim.setDuration(duration)
    fade_in_anim.setStartValue(0.0)
    fade_in_anim.setEndValue(1.0)

    group.addAnimation(fade_out)
    group.addAnimation(fade_in_anim)
    group.start(QAbstractAnimation.DeleteWhenStopped)
    return group
