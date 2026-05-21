from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_title(text: str, max_len: int = 32) -> str:
    normalized = " ".join(text.strip().split())
    if not normalized:
        return "新会话"
    if len(normalized) <= max_len:
        return normalized
    return normalized[:max_len].rstrip() + "..."


def json_dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def json_load(raw: str | None, default: Any) -> Any:
    if not raw:
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return default


def parse_iso_datetime(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


@dataclass
class Conversation:
    id: str
    owner_id: str
    title: str
    last_user_text: str
    created_at: str
    updated_at: str
    last_message_at: str
    metadata: dict[str, Any]
    message_count: int = 0
    last_message_preview: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "title": self.title,
            "last_user_text": self.last_user_text,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_message_at": self.last_message_at,
            "metadata": self.metadata,
            "message_count": self.message_count,
            "last_message_preview": self.last_message_preview,
        }


@dataclass
class ConversationMessage:
    id: str
    conversation_id: str
    role: str
    content: str
    created_at: str
    status: str
    response_id: str | None
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at,
            "status": self.status,
            "response_id": self.response_id,
            "metadata": self.metadata,
        }
