import asyncio
from datetime import datetime, timezone
from typing import Any

MAX_REPLAY_EVENTS = 200
TERMINAL_EVENTS = {"completed", "failed"}


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


class EventBus:
    """In-process fan-out of run events, one channel per research session.

    A replay buffer is kept so a browser that subscribes after the run started still
    receives every event it missed.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[asyncio.Queue]] = {}
        self._replay: dict[str, list[dict[str, Any]]] = {}
        self._finished: set[str] = set()

    def subscribe(self, session_id: str) -> tuple[asyncio.Queue, list[dict[str, Any]]]:
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers.setdefault(session_id, []).append(queue)
        return queue, list(self._replay.get(session_id, []))

    def unsubscribe(self, session_id: str, queue: asyncio.Queue) -> None:
        queues = self._subscribers.get(session_id)
        if not queues:
            return
        if queue in queues:
            queues.remove(queue)
        if not queues:
            self._subscribers.pop(session_id, None)

    def is_finished(self, session_id: str) -> bool:
        return session_id in self._finished

    async def publish(self, session_id: str, event: dict[str, Any]) -> None:
        payload = {"session_id": session_id, "ts": _timestamp(), **event}
        buffer = self._replay.setdefault(session_id, [])
        buffer.append(payload)
        if len(buffer) > MAX_REPLAY_EVENTS:
            del buffer[0 : len(buffer) - MAX_REPLAY_EVENTS]
        if payload.get("type") in TERMINAL_EVENTS:
            self._finished.add(session_id)
        for queue in list(self._subscribers.get(session_id, [])):
            await queue.put(payload)

    def clear(self, session_id: str) -> None:
        self._replay.pop(session_id, None)
        self._finished.discard(session_id)
        self._subscribers.pop(session_id, None)


event_bus = EventBus()
