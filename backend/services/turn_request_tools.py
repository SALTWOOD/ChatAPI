from __future__ import annotations

from typing import Any


def extract_tool_names(data: dict[str, Any]) -> set[str]:
    raw_tools = data.get("tools")
    if not isinstance(raw_tools, list):
        return set()

    names: set[str] = set()
    for tool in raw_tools:
        if not isinstance(tool, dict):
            continue
        func = tool.get("function")
        if isinstance(func, dict):
            name = func.get("name")
        else:
            name = tool.get("name")
        if isinstance(name, str) and name.strip():
            names.add(name.strip())
    return names


def extract_tool_schemas(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw_tools = data.get("tools")
    if not isinstance(raw_tools, list):
        return {}

    schemas: dict[str, dict[str, Any]] = {}
    for tool in raw_tools:
        if not isinstance(tool, dict):
            continue
        func = tool.get("function")
        if isinstance(func, dict):
            name = func.get("name")
            parameters = func.get("parameters", {})
        else:
            name = tool.get("name")
            parameters = tool.get("input_schema", {})
        if isinstance(name, str) and name.strip():
            schemas[name.strip()] = parameters if isinstance(parameters, dict) else {}
    return schemas


def find_response_message_metadata(messages: list[Any], response_id: str) -> dict[str, Any]:
    for message in reversed(messages):
        if message.response_id == response_id and message.role == "assistant":
            return dict(message.metadata)
    return {}
