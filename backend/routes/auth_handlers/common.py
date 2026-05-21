from __future__ import annotations

import hashlib
import hmac
import secrets
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from logging import Logger

from flask import current_app
from ...core import AuthContext, Settings
from ...repositories import SystemConfigStore, UserStore


_verification_codes: dict[str, tuple[str, float]] = {}
_CODE_TTL = 300


@dataclass(frozen=True)
class AuthRouteDeps:
    auth: AuthContext
    settings: Settings
    system_config_store: SystemConfigStore
    user_store: UserStore


def get_logger() -> Logger:
    return current_app.logger


def cleanup_expired_codes() -> None:
    now = time.time()
    expired = [email for email, (_, exp) in _verification_codes.items() if now > exp]
    for email in expired:
        del _verification_codes[email]


def verification_code_key(*, purpose: str, email: str) -> str:
    return f"{purpose}:{email.strip().lower()}"


def store_verification_code(*, purpose: str, email: str, code: str) -> None:
    _verification_codes[verification_code_key(purpose=purpose, email=email)] = (
        code,
        time.time() + _CODE_TTL,
    )


def consume_verification_code(*, purpose: str, email: str, code: str) -> str | None:
    stored = _verification_codes.get(verification_code_key(purpose=purpose, email=email))
    if stored is None:
        return "请先获取验证码"
    stored_code, expiry = stored
    if time.time() > expiry:
        del _verification_codes[verification_code_key(purpose=purpose, email=email)]
        return "验证码已过期，请重新获取"
    if code != stored_code:
        return "验证码不正确"
    del _verification_codes[verification_code_key(purpose=purpose, email=email)]
    return None


def verify_geetest(settings: Settings, geetest_params: object, logger: Logger) -> str | None:
    if not settings.geetest_captcha_id:
        return None
    if not geetest_params or not isinstance(geetest_params, dict):
        return "请完成人机验证"

    lot_number = str(geetest_params.get("lot_number", ""))
    captcha_output = str(geetest_params.get("captcha_output", ""))
    pass_token = str(geetest_params.get("pass_token", ""))
    gen_time = str(geetest_params.get("gen_time", ""))

    if not all([lot_number, captcha_output, pass_token, gen_time]):
        return "人机验证参数不完整"

    sign_token = hmac.new(
        settings.geetest_captcha_key.encode(),
        lot_number.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()

    params = {
        "lot_number": lot_number,
        "captcha_output": captcha_output,
        "pass_token": pass_token,
        "gen_time": gen_time,
        "sign_token": sign_token,
    }
    api_url = f"{settings.geetest_api_server}/validate?captcha_id={settings.geetest_captcha_id}"

    try:
        encoded = urllib.parse.urlencode(params).encode()
        req = urllib.request.Request(api_url, data=encoded, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = resp.read().decode()
        import json as _json

        gt_result = _json.loads(result)
    except Exception as exc:
        logger.warning("[GeeTest] validation request failed: %s", exc)
        gt_result = {"result": "success", "reason": "request geetest api fail"}

    if gt_result.get("result") != "success":
        return "人机验证失败，请重试"

    return None


def check_registration_email_domain(
    system_config_store: SystemConfigStore,
    email: str,
) -> str | None:
    if system_config_store.is_registration_email_allowed(email):
        return None
    domains = system_config_store.get_registration_email_domains()
    if not domains:
        return "当前已开启邮箱域名限制，但未配置允许的域名"
    return "该邮箱域名不允许注册"


def make_verification_code() -> str:
    return f"{secrets.randbelow(1000000):06d}"
