from __future__ import annotations

from urllib.parse import urlsplit

from flask import Flask, jsonify, request, session

SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}


def _first_header_value(value: str) -> str:
    return value.split(",", 1)[0].strip()


def _normalize_origin(value: str) -> str | None:
    raw = value.strip()
    if not raw or raw == "null":
        return None
    try:
        parsed = urlsplit(raw)
        if not parsed.scheme or not parsed.netloc:
            return None
        scheme = parsed.scheme.lower()
        if scheme not in {"http", "https"}:
            return None
        hostname = parsed.hostname
        if not hostname:
            return None
        port = parsed.port
    except ValueError:
        return None

    if port is None:
        port = 443 if scheme == "https" else 80
    return f"{scheme}://{hostname.lower()}:{port}"


def _request_origins() -> set[str]:
    origins: set[str] = set()

    forwarded_proto = _first_header_value(request.headers.get("X-Forwarded-Proto", ""))
    scheme = forwarded_proto or request.scheme
    current_origin = _normalize_origin(f"{scheme}://{request.host}")
    if current_origin:
        origins.add(current_origin)

    host_origin = _normalize_origin(request.host_url)
    if host_origin:
        origins.add(host_origin)

    return origins


def _configured_origins(cors_origins: list[str] | tuple[str, ...]) -> set[str]:
    origins: set[str] = set()
    for raw_origin in cors_origins:
        raw = str(raw_origin).strip()
        if not raw or raw == "*":
            continue
        normalized = _normalize_origin(raw)
        if normalized:
            origins.add(normalized)
    return origins


def _source_is_allowed(value: str, allowed_origins: set[str]) -> bool:
    normalized = _normalize_origin(value)
    return normalized is not None and normalized in allowed_origins


def register_csrf_protection(app: Flask, *, cors_origins: list[str] | tuple[str, ...]) -> None:
    configured_origins = _configured_origins(cors_origins)

    @app.before_request
    def reject_cross_site_session_mutations():
        if request.method in SAFE_METHODS:
            return None
        if not request.path.startswith("/api/"):
            return None
        allowed_origins = _request_origins() | configured_origins
        origin = request.headers.get("Origin", "").strip()
        if origin:
            if _source_is_allowed(origin, allowed_origins):
                return None
            app.logger.warning("Rejected cross-site request from Origin %s", origin)
            return jsonify({"error": "csrf_origin_mismatch"}), 403

        referer = request.headers.get("Referer", "").strip()
        if referer:
            if _source_is_allowed(referer, allowed_origins):
                return None
            app.logger.warning("Rejected cross-site request from Referer %s", referer)
            return jsonify({"error": "csrf_referer_mismatch"}), 403

        if not session.get("user_id"):
            return None

        app.logger.warning("Rejected session request without trusted Origin or Referer")
        return jsonify({"error": "csrf_origin_required"}), 403
