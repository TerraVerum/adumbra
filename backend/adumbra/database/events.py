import datetime
import time

from mongoengine import EmbeddedDocument, fields


class Event(EmbeddedDocument):

    name = fields.StringField()
    created_at = fields.DateTimeField()

    meta = {"allow_inheritance": True}

    def now(self, event):
        del event
        self.created_at = datetime.datetime.now()


class SessionEvent(Event):

    user = fields.StringField(required=True)
    milliseconds = fields.IntField(default=0, min_value=0)
    tools_used = fields.ListField(default=[])

    @classmethod
    def create(cls, start, user, end=None, tools: list[str] | None = None):
        del tools
        if end is None:
            end = time.time()

        return SessionEvent(user=user.username, milliseconds=int((end - start) * 1000))


__all__ = ["Event", "SessionEvent"]
