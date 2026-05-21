from __future__ import annotations

from typing import Any

from .models import parse_iso_datetime


def estimate_tokens(text: str) -> int:
    text = text.strip()
    if not text:
        return 0
    ascii_tokens = len(text.split())
    cjk_chars = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    return max(ascii_tokens, 1) + cjk_chars // 2


def estimate_usage(input_text: str, output_text: str) -> dict[str, int]:
    input_tokens = estimate_tokens(input_text)
    output_tokens = estimate_tokens(output_text)
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
    }


class StatisticsMixin:
    def get_statistics_summary(
        self,
        owner_id: str,
        *,
        start_at: str | None = None,
        end_at: str | None = None,
    ) -> dict[str, Any]:
        start_dt = parse_iso_datetime(start_at or "")
        end_dt = parse_iso_datetime(end_at or "")

        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT
                    m.conversation_id,
                    m.role,
                    m.content,
                    m.created_at,
                    m.response_id
                FROM messages m
                JOIN conversations c ON c.id = m.conversation_id
                WHERE c.owner_id = ?
                ORDER BY
                    m.conversation_id ASC,
                    datetime(m.created_at) ASC,
                    CASE
                        WHEN m.role = 'user' THEN 0
                        WHEN m.role = 'assistant' THEN 1
                        ELSE 2
                    END ASC,
                    m.id ASC
                """,
                (owner_id,),
            ).fetchall()

        latest_user_messages: dict[str, dict[str, Any]] = {}
        total_requests = 0
        total_input_tokens = 0
        total_output_tokens = 0
        total_tokens = 0
        total_request_seconds = 0.0

        for row in rows:
            conversation_id = str(row["conversation_id"])
            created_at = parse_iso_datetime(str(row["created_at"] or ""))
            if created_at is None:
                continue

            role = str(row["role"] or "")
            content = str(row["content"] or "")

            if role == "user":
                latest_user_messages[conversation_id] = {
                    "content": content,
                    "created_at": created_at,
                }
                continue

            if role != "assistant":
                continue

            if not str(row["response_id"] or "").strip():
                continue
            if start_dt is not None and created_at < start_dt:
                continue
            if end_dt is not None and created_at > end_dt:
                continue

            user_message = latest_user_messages.get(conversation_id)
            if user_message is None:
                continue

            usage = estimate_usage(str(user_message["content"]), content)
            duration_seconds = max(
                0.0,
                (created_at - user_message["created_at"]).total_seconds(),
            )

            total_requests += 1
            total_input_tokens += usage["input_tokens"]
            total_output_tokens += usage["output_tokens"]
            total_tokens += usage["total_tokens"]
            total_request_seconds += duration_seconds

        average_request_time_seconds = (
            total_request_seconds / total_requests if total_requests else 0.0
        )
        average_tpm = (
            total_output_tokens / (total_request_seconds / 60.0)
            if total_request_seconds > 0
            else 0.0
        )
        return {
            "total_requests": total_requests,
            "average_request_time_seconds": average_request_time_seconds,
            "average_tpm": average_tpm,
            "total_tokens": total_tokens,
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
            "start_at": start_at,
            "end_at": end_at,
        }
