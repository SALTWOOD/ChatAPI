from __future__ import annotations

from pathlib import Path

from flask import Flask, abort, send_from_directory

from ..core import AppDependencies


def register_upload_routes(app: Flask, *, deps: AppDependencies) -> None:
    auth = deps.auth
    image_store = deps.image_store

    @app.get("/api/uploads/imgs/<path:filename>")
    @auth.require_auth
    def get_uploaded_image(filename: str):
        safe_name = Path(filename).name
        if safe_name != filename or not safe_name:
            abort(404)
        path = image_store.base_dir / safe_name
        if not path.is_file():
            abort(404)
        return send_from_directory(image_store.base_dir, safe_name)
