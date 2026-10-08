from dataclasses import dataclass
from datetime import datetime


@dataclass
class Commit:
    """커밋 정보와 부모 연결."""

    hash: str
    message: str
    author: str
    timestamp: datetime
    parents: list[str]
