from fastapi import WebSocket
import uuid
import json
from Player import Player
import asyncio
import logging

class FrontEndConnector:
    def __init__(self, ws: WebSocket):
        self.ws = ws
        self.current_token: str | None = None
        self._lock = asyncio.Lock()
        self.logger = logging.getLogger("__name__")
        logging.basicConfig(filename="game.log", level=logging.DEBUG)
        self.logger.setLevel(logging.DEBUG)
    """
    Sends a message to the front-end
    Logs the player and then the message
    """
    async def send_message(self, message: str) -> None:
        await self.ws.send_text(json.dumps({
            "type": "chat_message",
            "note": message
        }))

    """
    Asks for a message on the front end and returns the player's response
    """
    async def ask_for_message(self, prompt: str) -> str:
        self.logger.debug(f"ask_for_message called with prompt: {prompt}")
        async with self._lock:
            self.logger.debug("Acquired lock for ask_for_message")
            self.current_token = uuid.uuid4().hex
            await self.ws.send_text(json.dumps({
                "type": "prompt_for_message",
                "prompt": prompt,
                "send_token": self.current_token
            }))

            raw = await self.ws.receive_text()
            data = json.loads(raw)

            if data.get("type") != "client_message":
                await self.ws.send_text(json.dumps({
                    "type": "error",
                    "detail": "Invalid message type"
                }))
                self.current_token = None
                return ''

            token = data.get("send_token")
            text = (data.get("text") or "").strip()

            # Enforce: client can only send when server has asked (token matches)
            if not self.current_token or token != self.current_token:
                await self.ws.send_text(json.dumps({
                    "type": "error",
                    "detail": "Client is locked or token is invalid"
                }))
                self.current_token = None
                return ''

            self.current_token = None

            return text
    
    async def ask_for_select(self, prompt: str, options: list[str]) -> str:
        self.logger.debug(f"ask_for_select called with prompt: {prompt} and options: {options}")    
        async with self._lock:
            self.logger.debug("Acquired lock for ask_for_select")
            self.current_token = uuid.uuid4().hex

            await self.ws.send_text(json.dumps({
                "type": "prompt_select",
                "prompt": prompt,
                "options": options,
                "send_token": self.current_token
            }))

            self.logger.debug("Message sent! Waiting for client selection...")

            raw = await self.ws.receive_text()
            data = json.loads(raw)

            if data.get("type") != "client_select":
                await self.ws.send_text(json.dumps({"type": "error", "detail": "Invalid message type"}))
                self.current_token = None
                return ""

            if data.get("send_token") != self.current_token:
                await self.ws.send_text(json.dumps({"type": "error", "detail": "Token invalid"}))
                self.current_token = None
                return ""

            value = (data.get("value") or "").strip()

            if value not in options:
                await self.ws.send_text(json.dumps({"type": "error", "detail": "Invalid selection"}))
                self.current_token = None
                return ""

            self.current_token = None
            return value
