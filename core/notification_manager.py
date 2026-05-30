"""
Notification Manager — catalogs and announces system alerts.
"""
import time
from dataclasses import dataclass, field
from typing import Any
from logger_config import setup_logger

logger = setup_logger("notification_manager")

@dataclass
class Notification:
    title: str
    message: str
    category: str = "info"
    source: str = "system"
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
    read: bool = False

class NotificationManager:
    VALID_CATEGORIES = {"info", "warning", "critical"}

    def __init__(self, memory=None):
        self.memory = memory
        self.notifications: list[Notification] = []
        logger.info("NotificationManager initialized.")

    def notify(self, title: str, message: str, category: str = "info", source: str = "system") -> Notification:
        category = category if category in self.VALID_CATEGORIES else "info"
        notification = Notification(title=title, message=message, category=category, source=source)
        self.notifications.append(notification)
        logger.info(f"New notification: {title} ({category})")
        if self.memory:
            self.memory.add_notification(notification.__dict__)
        return notification

    def get_notifications(self, category: str | None = None) -> list[Notification]:
        if category:
            return [n for n in self.notifications if n.category == category]
        return list(self.notifications)

    def get_unread(self) -> list[Notification]:
        return [n for n in self.notifications if not n.read]

    def mark_as_read(self, notification: Notification):
        notification.read = True
        logger.info(f"Marked notification read: {notification.title}")
