from __future__ import annotations

from pathlib import Path

from flask import Flask, Response, abort, send_from_directory

from ..core import AppDependencies

EXPIRED_IMAGE_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="640" height="360" viewBox="0 0 640 360">
  <rect width="640" height="360" rx="24" fill="#f1f5f9"/>
  <rect x="24" y="24" width="592" height="312" rx="18" fill="#e2e8f0"/>
  <text x="320" y="170" text-anchor="middle" font-family="sans-serif" font-size="28" fill="#334155">图片已过期</text>
  <text x="320" y="212" text-anchor="middle" font-family="sans-serif" font-size="16" fill="#64748b">原始图片已被容量策略清理或未保存</text>
</svg>"""


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
            return Response(EXPIRED_IMAGE_SVG, mimetype="image/svg+xml", status=410)
        return send_from_directory(image_store.base_dir, safe_name)

    @app.get("/api/uploads/imgs/usage")
    @auth.require_admin
    def get_upload_image_usage():
        return {
            "ok": True,
            "usage": image_store.storage_usage(deps.store.iter_messages()),
        }
