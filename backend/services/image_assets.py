from __future__ import annotations

import base64
import binascii
import hashlib
import json
import re
from pathlib import Path
from typing import Any


_DATA_IMAGE_RE = re.compile(r"^data:(image/[a-zA-Z0-9.+-]+);base64,(.+)$", re.IGNORECASE | re.DOTALL)


def _normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _mime_to_extension(mime_type: str) -> str:
    normalized = mime_type.lower().split(";", 1)[0].strip()
    mapping = {
        "image/jpeg": "jpg",
        "image/jpg": "jpg",
        "image/png": "png",
        "image/gif": "gif",
        "image/webp": "webp",
        "image/avif": "avif",
        "image/bmp": "bmp",
        "image/svg+xml": "svg",
        "image/tiff": "tiff",
    }
    return mapping.get(normalized, normalized.rsplit("/", 1)[-1] or "img")


def _mime_from_magic(image_bytes: bytes) -> str | None:
    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if image_bytes.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if image_bytes.startswith(b"GIF87a") or image_bytes.startswith(b"GIF89a"):
        return "image/gif"
    if image_bytes.startswith(b"RIFF") and image_bytes[8:12] == b"WEBP":
        return "image/webp"
    if image_bytes.startswith(b"BM"):
        return "image/bmp"
    if image_bytes.startswith(b"\x00\x00\x00") and b"ftypavif" in image_bytes[:32]:
        return "image/avif"
    if image_bytes.lstrip().startswith(b"<?xml") or b"<svg" in image_bytes[:256].lower():
        return "image/svg+xml"
    return None


def _is_image_key(key: str) -> bool:
    normalized = _normalize_key(key)
    return any(token in normalized for token in ("image", "img", "photo", "picture", "thumbnail", "avatar", "filedata", "basedata", "binary"))


def _looks_like_base64(value: str) -> bool:
    candidate = re.sub(r"\s+", "", value)
    if len(candidate) < 32 or len(candidate) % 4 != 0:
        return False
    return bool(re.fullmatch(r"[A-Za-z0-9+/=]+", candidate))


def _try_parse_structured_content(raw: str) -> Any | None:
    try:
        return json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        pass

    trimmed = raw.strip()
    if not trimmed or trimmed[0] not in "[{":
        return None

    normalized = ""
    in_single_quote = False
    in_double_quote = False
    escape_next = False

    for char in trimmed:
        if escape_next:
            normalized += char
            escape_next = False
            continue
        if char == "\\":
            normalized += char
            escape_next = True
            continue
        if char == "'" and not in_double_quote:
            normalized += '"'
            in_single_quote = not in_single_quote
            continue
        if char == '"' and not in_single_quote:
            normalized += char
            in_double_quote = not in_double_quote
            continue
        normalized += '\\"' if in_single_quote and char == '"' else char

    normalized = normalized.replace("None", "null").replace("True", "true").replace("False", "false")
    try:
        return json.loads(normalized)
    except (TypeError, json.JSONDecodeError):
        return None


def _decode_base64_image(value: str, *, mime_type_hint: str | None = None) -> tuple[bytes, str] | None:
    text = value.strip()
    data_url_match = _DATA_IMAGE_RE.match(text)
    if data_url_match:
        mime_type = data_url_match.group(1)
        payload = data_url_match.group(2)
    else:
        if not _looks_like_base64(text):
            return None
        mime_type = mime_type_hint or ""
        payload = text
    try:
        image_bytes = base64.b64decode(payload, validate=False)
    except (binascii.Error, ValueError):
        return None
    detected_mime = _mime_from_magic(image_bytes)
    if detected_mime is not None:
        mime_type = detected_mime
    if not mime_type.startswith("image/"):
        return None
    return image_bytes, mime_type


class ImageAssetStore:
    def __init__(self, base_dir: Path, route_prefix: str = "/api/uploads/imgs"):
        self.base_dir = base_dir
        self.route_prefix = route_prefix.rstrip("/")
        self.base_dir.mkdir(parents=True, exist_ok=True)

    @property
    def route_root(self) -> str:
        return self.route_prefix

    def public_url(self, filename: str) -> str:
        return f"{self.route_root}/{filename}"

    def _filename_for(self, image_bytes: bytes, mime_type: str) -> str:
        digest = hashlib.sha256(image_bytes).hexdigest()
        ext = _mime_to_extension(mime_type)
        return f"{digest}.{ext}"

    def store_data_url(self, value: str) -> str | None:
        decoded = _decode_base64_image(value)
        if decoded is None:
            return None
        image_bytes, mime_type = decoded
        filename = self._filename_for(image_bytes, mime_type)
        path = self.base_dir / filename
        if not path.exists():
            path.write_bytes(image_bytes)
        return self.public_url(filename)

    def normalize_request_data(self, value: Any) -> Any:
        return self._normalize_node(value)

    def _rewrite_string(self, value: str, *, key: str = "") -> str:
        data_url_url = self.store_data_url(value)
        if data_url_url is not None:
            return data_url_url

        decoded = _decode_base64_image(value)
        if decoded is not None:
            image_bytes, mime_type = decoded
            filename = self._filename_for(image_bytes, mime_type)
            path = self.base_dir / filename
            if not path.exists():
                path.write_bytes(image_bytes)
            return self.public_url(filename)

        if _is_image_key(key):
            decoded = _decode_base64_image(value)
            if decoded is not None:
                image_bytes, mime_type = decoded
                filename = self._filename_for(image_bytes, mime_type)
                path = self.base_dir / filename
                if not path.exists():
                    path.write_bytes(image_bytes)
                return self.public_url(filename)
        return value

    def _normalize_node(self, value: Any, *, key: str = "") -> Any:
        if isinstance(value, str):
            parsed = _try_parse_structured_content(value)
            if parsed is not None:
                return self._normalize_node(parsed, key=key)
            return self._rewrite_string(value, key=key)
        if isinstance(value, list):
            return [self._normalize_node(item, key=key) for item in value]
        if isinstance(value, dict):
            rewritten: dict[str, Any] = {}
            for item_key, item_value in value.items():
                rewritten[item_key] = self._normalize_node(item_value, key=str(item_key))
            return rewritten
        return value

    def rewrite_value(self, value: Any, *, key: str = "") -> Any:
        return self._normalize_node(value, key=key)

    def normalize_content(self, content: Any) -> str:
        if isinstance(content, str):
            parsed = _try_parse_structured_content(content)
            if parsed is not None:
                rewritten = self.rewrite_value(parsed, key="content")
                return json.dumps(rewritten, ensure_ascii=False, separators=(",", ":"))
        rewritten = self.rewrite_value(content, key="content")
        if isinstance(rewritten, str):
            return rewritten.replace("\r\n", "\n").replace("\\r\\n", "\n").replace("\\n", "\n")
        return json.dumps(rewritten, ensure_ascii=False, separators=(",", ":"))

    def referenced_filenames(self, content: str) -> set[str]:
        if not content:
            return set()
        pattern = re.compile(
            rf"(?:https?://[^\s\"']+)?{re.escape(self.route_root)}/([A-Za-z0-9._-]+)",
            re.IGNORECASE,
        )
        return {match.group(1) for match in pattern.finditer(content)}

    def cleanup_orphans(self, messages: list[Any]) -> list[str]:
        referenced: set[str] = set()
        for message in messages:
            content = getattr(message, "content", "")
            if isinstance(content, str):
                referenced.update(self.referenced_filenames(content))

        deleted: list[str] = []
        if not self.base_dir.exists():
            return deleted

        for path in self.base_dir.iterdir():
            if not path.is_file():
                continue
            if path.name in referenced:
                continue
            path.unlink(missing_ok=True)
            deleted.append(path.name)
        return deleted
