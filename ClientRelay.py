import asyncio
import json
import logging
import os

from redis.asyncio import Redis

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_TLS = os.getenv("REDIS_TLS", "false").lower() == "true"

logger = logging.getLogger("game")


class ClientRelay:
    def __init__(self, dest: str):
        self.redis = Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            ssl=REDIS_TLS,
            decode_responses=True,
        )
        self.dest = dest
        self.pubsub = self.redis.pubsub()
        self._subscribed = False
        self._lock = asyncio.Lock()

    async def _ensure_subscribed(self) -> None:
        if not self._subscribed:
            await self.pubsub.subscribe(f"{self.dest}:in")
            self._subscribed = True

    async def _publish(self, payload: dict) -> None:
        await self.redis.publish(f"{self.dest}:out", json.dumps(payload))

    async def _receive(self, expected_type: str, timeout: float = 60) -> dict | None:
        await self._ensure_subscribed()
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout
        while loop.time() < deadline:
            raw = await self.pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=min(1, max(0, deadline - loop.time())),
            )
            if raw is None:
                await asyncio.sleep(0.02)
                continue
            payload = json.loads(raw["data"])
            if payload.get("type") == expected_type:
                return payload
        return None

    async def send_message(self, message: str) -> None:
        await self._publish({"type": "chat_message", "note": message})

    async def send_chat_message(self, message: str, player_name: str) -> None:
        await self._publish({
            "type": "player_chat_message",
            "note": message,
            "player": player_name,
        })

    async def report_player_killed(self, player_name: str) -> None:
        await self._publish({"type": "player_killed", "player": player_name})

    async def send_player_list(self, player_names: list[str]) -> None:
        await self._publish({"type": "player_list", "players": player_names})

    async def ask_for_message(self, prompt: str) -> str:
        async with self._lock:
            await self._ensure_subscribed()
            await self._publish({"type": "prompt_for_message", "prompt": prompt})
            response = await self._receive("client_message")
            if response is None:
                return ""
            text = (response.get("text") or "").strip()
            return text if len(text) <= 200 else ""

    async def ask_for_select(self, prompt: str, options: list[str]) -> str:
        async with self._lock:
            await self._ensure_subscribed()
            await self._publish({
                "type": "prompt_select",
                "prompt": prompt,
                "options": options,
            })
            response = await self._receive("client_select")
            if response is None:
                return ""
            value = (response.get("value") or "").strip()
            return value if value in options else ""

    async def close(self) -> None:
        await self.pubsub.aclose()
        await self.redis.aclose()
