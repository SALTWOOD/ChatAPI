from __future__ import annotations

import time


def build_chat_completion_response(
    *,
    response_id: str,
    model: str,
    assistant_text: str,
    usage: dict[str, int] | None,
    response_mode: str = "assistant_message",
    tool_name: str = "",
    tool_call_id: str = "",
    arguments: str = "",
) -> dict[str, object]:
    finish_reason = "stop"
    message: dict[str, object] = {
        "role": "assistant",
        "content": assistant_text,
    }
    if response_mode == "tool_call":
        finish_reason = "tool_calls"
        message = {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": tool_call_id,
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "arguments": arguments,
                    },
                }
            ],
        }
    return {
        "id": response_id,
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": message,
                "finish_reason": finish_reason,
            }
        ],
        "usage": {
            "prompt_tokens": usage["input_tokens"] if usage else 0,
            "completion_tokens": usage["output_tokens"] if usage else 0,
            "total_tokens": usage["total_tokens"] if usage else 0,
        },
    }
