from __future__ import annotations

import base64
import io

from flask import Flask, jsonify, request

from ...core.auth import build_totp_uri, generate_totp_secret, verify_totp_code
from .common import AuthRouteDeps


def register_totp_routes(app: Flask, deps: AuthRouteDeps) -> None:
    @app.get("/api/auth/totp/setup")
    @deps.auth.require_session_auth
    def totp_setup():
        user = deps.auth.current_user()
        if user is None:
            return jsonify({"error": "unauthorized"}), 401

        db_user = deps.user_store.get_user(user["id"])
        if db_user is None:
            return jsonify({"error": "user not found"}), 404

        if db_user.totp_secret:
            return jsonify({"error": "TOTP 已启用，请先重置"}), 400

        secret = generate_totp_secret()
        uri = build_totp_uri(secret, db_user.username)

        try:
            import qrcode

            img = qrcode.make(uri)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            qr_base64 = base64.b64encode(buf.getvalue()).decode()
        except ImportError:
            qr_base64 = ""

        return {
            "ok": True,
            "secret": secret,
            "uri": uri,
            "qr_base64": qr_base64,
        }

    @app.post("/api/auth/totp/confirm")
    @deps.auth.require_session_auth
    def totp_confirm():
        user = deps.auth.current_user()
        if user is None:
            return jsonify({"error": "unauthorized"}), 401

        data = request.get_json(silent=True) or {}
        secret = str(data.get("secret", "")).strip()
        code = str(data.get("code", "")).strip()

        if not secret or not code:
            return jsonify({"error": "secret 和 code 不能为空"}), 400

        if not verify_totp_code(secret, code):
            return jsonify({"error": "验证码不正确"}), 400

        deps.user_store.update_user_totp_secret(user["id"], secret)
        return {"ok": True}

    @app.post("/api/auth/totp/reset")
    @deps.auth.require_session_auth
    def totp_reset():
        user = deps.auth.current_user()
        if user is None:
            return jsonify({"error": "unauthorized"}), 401

        deps.user_store.update_user_totp_secret(user["id"], "")
        return {"ok": True}
