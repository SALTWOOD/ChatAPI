from .common import AuthRouteDeps
from .password_routes import register_password_routes
from .register_routes import register_registration_routes
from .session_routes import register_session_routes
from .totp_routes import register_totp_routes

__all__ = [
    "AuthRouteDeps",
    "register_password_routes",
    "register_registration_routes",
    "register_session_routes",
    "register_totp_routes",
]
