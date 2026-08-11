from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Notification:
    title: str
    message: str
    level: str = "info"
    timestamp: datetime = field(default_factory=datetime.now)


class NotificationCenter:
    def __init__(self):
        self.notifications = []

    def add(self, title: str, message: str, level: str = "info"):
        note = Notification(title=title, message=message, level=level)
        self.notifications.append(note)
        return note

    def latest(self, limit: int = 20):
        return list(reversed(self.notifications[-limit:]))

    def count(self):
        return len(self.notifications)


notification_center = NotificationCenter()
