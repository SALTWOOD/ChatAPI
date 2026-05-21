from __future__ import annotations

from flask import Flask, jsonify, request

from ...services.email import (
    get_available_email_providers,
    resolve_email_provider,
    send_verification_email,
)
from .common import (
    AuthRouteDeps,
    cleanup_expired_codes,
    consume_verification_code,
    get_logger,
    make_verification_code,
    store_verification_code,
    verify_geetest,
)


def register_password_routes(app: Flask, deps: AuthRouteDeps) -> None:
    @app.get("/api/auth/password/config")
    def password_reset_config():
        available_email_providers = get_available_email_providers()
        provider = resolve_email_provider(
            deps.system_config_store.get_system_config("value.email_provider", ""),
            available_email_providers,
        )
        geetest_enabled = bool(deps.settings.geetest_captcha_id)
        return {
            "ok": True,
            "password_reset_enabled": bool(provider),
            "geetest_enabled": geetest_enabled,
            "geetest_captcha_id": deps.settings.geetest_captcha_id if geetest_enabled else "",
        }

    @app.post("/api/auth/password/send-code")
    def password_send_code():
        data = request.get_json(silent=True) or {}
        email = str(data.get("email", "")).strip().lower()
        geetest_params = data.get("geetest_params")

        if not email or "@" not in email:
            return jsonify({"error": "请输入有效的邮箱地址"}), 400

        available_email_providers = get_available_email_providers()
        provider = resolve_email_provider(
            deps.system_config_store.get_system_config("value.email_provider", ""),
            available_email_providers,
        )
        if not provider:
            return jsonify({"error": "当前未配置找回密码所需的邮件发送方式"}), 403

        geetest_error = verify_geetest(deps.settings, geetest_params, get_logger())
        if geetest_error is not None:
            return jsonify({"error": geetest_error}), 400

        user = deps.user_store.get_user_by_username(email)
        if user is None:
            return jsonify({"error": "该邮箱未注册"}), 400

        cleanup_expired_codes()
        code = make_verification_code()
        store_verification_code(purpose="password_reset", email=email, code=code)

        ok, message = send_verification_email(email, code, provider=provider, logger=get_logger())
        if not ok:
            return jsonify({"error": message}), 400

        return {"ok": True, "message": "验证码已发送"}

    @app.post("/api/auth/password/reset")
    def password_reset():
        data = request.get_json(silent=True) or {}
        email = str(data.get("email", "")).strip().lower()
        code = str(data.get("code", "")).strip()
        password = str(data.get("password", ""))

        if not email or "@" not in email:
            return jsonify({"error": "请输入有效的邮箱地址"}), 400
        if not code:
            return jsonify({"error": "请输入邮箱验证码"}), 400
        if len(password) < 4:
            return jsonify({"error": "密码至少需要 4 个字符"}), 400

        available_email_providers = get_available_email_providers()
        provider = resolve_email_provider(
            deps.system_config_store.get_system_config("value.email_provider", ""),
            available_email_providers,
        )
        if not provider:
            return jsonify({"error": "当前未配置找回密码所需的邮件发送方式"}), 403

        user = deps.user_store.get_user_by_username(email)
        if user is None:
            return jsonify({"error": "该邮箱未注册"}), 400

        code_error = consume_verification_code(purpose="password_reset", email=email, code=code)
        if code_error is not None:
            return jsonify({"error": code_error}), 400

        deps.user_store.update_user_password(user.id, password)
        return {"ok": True}
