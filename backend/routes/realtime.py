from __future__ import annotations

import json
import queue
from typing import Any

from flask import Flask
from flask_sock import Sock

from ..core import AppDependencies
from ..services.realtime import RealtimeBroker


def register_realtime_routes(app: Flask, *, deps: AppDependencies) -> None:
    auth = deps.auth
    system_config_store = deps.system_config_store
    sock = Sock(app)

    @sock.route("/api/ws")
    def websocket_sync(ws: Any) -> None:
        if auth.current_user() is None:
            ws.close()
            return

        owner = auth.owner_id()
        reconcile_waiting = app.extensions.get("chat_reconcile_waiting")
        realtime = app.extensions.get("chat_realtime")
        if not callable(reconcile_waiting) or not isinstance(realtime, RealtimeBroker):
            ws.close()
            return

        subscription = realtime.subscribe(
            owner,
            max_connections=system_config_store.get_system_config("value.realtime_max_connections", "0"),
            max_connections_per_user=system_config_store.get_system_config("value.realtime_max_connections_per_user", "0"),
            queue_size=system_config_store.get_system_config("value.realtime_queue_size", "100"),
        )

        try:
            reconcile_waiting(owner)
            ws.send(
                json.dumps(
                    realtime.build_snapshot(owner),
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
            )

            while not subscription.closed.is_set():
                try:
                    event = subscription.events.get(timeout=20)
                    ws.send(json.dumps(event, ensure_ascii=False, separators=(",", ":")))
                except queue.Empty:
                    ws.send('{"type":"ping"}')
            ws.close()
        finally:
            realtime.unsubscribe(subscription)
