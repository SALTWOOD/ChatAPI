from __future__ import annotations

from flask import Flask, request

from ..core import AppDependencies

PUBLIC_STATISTICS_CONFIG_KEY = "system.public_statistics"


def register_statistics_routes(app: Flask, *, deps: AppDependencies) -> None:
    auth = deps.auth
    store = deps.store

    @app.get("/api/statistics/summary")
    def get_statistics_summary():
        public_statistics = store.get_config(PUBLIC_STATISTICS_CONFIG_KEY, "0") == "1"
        if not public_statistics and auth.current_user() is None and not auth.is_request_authorized_by_api_key():
            return {"error": "unauthorized"}, 401

        owner = "workspace:default"
        start_at = request.args.get("start") or None
        end_at = request.args.get("end") or None
        summary = store.get_statistics_summary(owner, start_at=start_at, end_at=end_at)
        return {
            "ok": True,
            "summary": summary,
        }
