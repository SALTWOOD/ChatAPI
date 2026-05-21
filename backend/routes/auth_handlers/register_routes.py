from __future__ import annotations

from flask import Flask, jsonify, request, session

from ...services.email import (
    get_available_email_providers,
    resolve_email_provider,
    send_verification_email,
)
from .common import (
    AuthRouteDeps,
    check_registration_email_domain,
    cleanup_expired_codes,
    consume_verification_code,
    get_logger,
    make_verification_code,
    store_verification_code,
    verify_geetest,
)


def register_registration_routes(app: Flask, deps: AuthRouteDeps) -> None:
    @app.get("/api/auth/register/config")
    def register_config():
        ext_reg = deps.system_config_store.get_system_config("flag.external_registration", "0") == "1"
        email_ver = deps.system_config_store.get_system_config("flag.email_verification", "0") == "1"
        domain_restriction = deps.system_config_store.get_system_config(
            "flag.registration_email_domain_restriction",
            "0",
        ) == "1"
        allowed_domains = ",".join(deps.system_config_store.get_registration_email_domains())
        geetest_enabled = bool(deps.settings.geetest_captcha_id)
        return {
            "ok": True,
            "registration_enabled": ext_reg,
            "email_verification_enabled": ext_reg and email_ver,
            "registration_email_domain_restriction_enabled": domain_restriction,
            "registration_email_domains": allowed_domains,
            "geetest_enabled": geetest_enabled,
            "geetest_captcha_id": deps.settings.geetest_captcha_id if geetest_enabled else "",
        }

    @app.post("/api/auth/register/send-code")
    def register_send_code():
        data = request.get_json(silent=True) or {}
        email = str(data.get("email", "")).strip().lower()
        geetest_params = data.get("geetest_params")

        if not email or "@" not in email:
            return jsonify({"error": "请输入有效的邮箱地址"}), 400

        ext_reg = deps.system_config_store.get_system_config("flag.external_registration", "0") == "1"
        if not ext_reg:
            return jsonify({"error": "注册功能未开放"}), 403

        domain_error = check_registration_email_domain(deps.system_config_store, email)
        if domain_error is not None:
            return jsonify({"error": domain_error}), 403

        existing = deps.user_store.get_user_by_username(email)
        if existing is not None:
            return jsonify({"error": "该邮箱已注册"}), 400

        geetest_error = verify_geetest(deps.settings, geetest_params, get_logger())
        if geetest_error is not None:
            return jsonify({"error": geetest_error}), 400

        cleanup_expired_codes()
        code = make_verification_code()
        store_verification_code(purpose="register", email=email, code=code)

        provider = resolve_email_provider(
            deps.system_config_store.get_system_config("value.email_provider", ""),
            get_available_email_providers(),
        )
        ok, message = send_verification_email(email, code, provider=provider, logger=get_logger())
        if not ok:
            return jsonify({"error": message}), 400

        return {"ok": True, "message": "验证码已发送"}

    @app.post("/api/auth/register")
    def register():
        data = request.get_json(silent=True) or {}
        email = str(data.get("email", "")).strip().lower()
        password = str(data.get("password", ""))
        code = str(data.get("code", "")).strip()
        geetest_params = data.get("geetest_params")

        if not email or "@" not in email:
            return jsonify({"error": "请输入有效的邮箱地址"}), 400
        if len(password) < 4:
            return jsonify({"error": "密码至少需要 4 个字符"}), 400

        ext_reg = deps.system_config_store.get_system_config("flag.external_registration", "0") == "1"
        if not ext_reg:
            return jsonify({"error": "注册功能未开放"}), 403

        domain_error = check_registration_email_domain(deps.system_config_store, email)
        if domain_error is not None:
            return jsonify({"error": domain_error}), 403

        existing = deps.user_store.get_user_by_username(email)
        if existing is not None:
            return jsonify({"error": "该邮箱已注册"}), 400

        email_ver = deps.system_config_store.get_system_config("flag.email_verification", "0") == "1"
        if not email_ver:
            geetest_error = verify_geetest(deps.settings, geetest_params, get_logger())
            if geetest_error is not None:
                return jsonify({"error": geetest_error}), 400

        if email_ver:
            if not code:
                return jsonify({"error": "请输入邮箱验证码"}), 400
            code_error = consume_verification_code(purpose="register", email=email, code=code)
            if code_error is not None:
                return jsonify({"error": code_error}), 400

        user = deps.user_store.create_user(email, password, role="user")
        session["user_id"] = user.id
        session["username"] = user.username
        session["role"] = user.role
        deps.user_store.update_last_login_at(user.id)
        return {"ok": True, "user": user.to_dict()}, 201
