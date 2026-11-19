from datetime import datetime, timezone
from uuid import uuid4


def new_id() -> str:
    return uuid4().hex


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
