from __future__ import annotations

from flask import Flask

from ..core import AuthContext, Settings
from ..repositories import SystemConfigStore, UserStore
from .auth_handlers import (
    AuthRouteDeps,
    register_password_routes,
    register_registration_routes,
    register_session_routes,
    register_totp_routes,
)


def register_auth_routes(
    app: Flask,
    *,
    auth: AuthContext,
    settings: Settings,
    system_config_store: SystemConfigStore,
    user_store: UserStore,
) -> None:
    deps = AuthRouteDeps(
        auth=auth,
        settings=settings,
        system_config_store=system_config_store,
        user_store=user_store,
    )
    register_registration_routes(app, deps)
    register_password_routes(app, deps)
    register_session_routes(app, deps)
    register_totp_routes(app, deps)
