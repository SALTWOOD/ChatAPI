from __future__ import annotations

from dataclasses import dataclass

from .auth import AuthContext
from .config import Settings
from ..repositories import ConversationStore
from ..services import MessageRateLimiter, PendingTurnRegistry
from ..services.image_assets import ImageAssetStore


@dataclass(frozen=True)
class AppDependencies:
    settings: Settings
    auth: AuthContext
    store: ConversationStore
    pending_turns: PendingTurnRegistry
    message_rate_limiter: MessageRateLimiter
    image_store: ImageAssetStore
