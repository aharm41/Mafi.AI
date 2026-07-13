import uuid
import json
from Player import Player
import asyncio
import logging
import os
from redis.asyncio import Redis

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_TLS = os.getenv("REDIS_TLS", "false").lower() == "true"

logger = logging.getLogger('game')

class ClientRelay:
    def __init__(self, dest: str):
        self.redis = Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            ssl=REDIS_TLS,
            decode_response=True,
        )
        
        self.pubsub = self.redis.pubsub()
        self.pubsub.subscribe(dest)
        
        self.dest = dest
        self.current_token: str | None = None
        self._lock = asyncio.Lock()
        
        
    """
    Sends a message to the front-end
    Logs the player and then the message    
    """
    async def send_message(self, message: str) -> None:
        logger.debug(f"send_message called with message: {message}")
        
        await self.redis.publish(self.dest, json.dumps({
            "type": "chat_message",
            "note": message,
        }))
        
        
    """
    Sends a chat message to the front-end with the player name attached
    """
    async def send_chat_message(self, message: str, player_name: str) -> None:
        logger.debug(f"send_chat_message called with message: {message} and player_name: {player_name}")
        
        await self.redis.publish(self.dest, json.dumps({
            "type": "player_chat_message",
            "note": message,
            "player": player_name
        }))
        
        
    """
    Reports that a player has been killed to the front-end
    """
    async def report_player_killed(self, player_name: str) -> None:
        await self.redis.publish(self.dest, json.dumps({
            "type": "player_killed",
            "player": player_name
        }))
        
        
    """
    Send a list of all the players at the start of the game
    """
    async def send_player_list(self, player_names: list[str]) -> None:
        await self.redis.publish(self.dest, json.dumps({
            "type": "player_list",
            "players": player_names
        }))
    

    """
    Asks for a message on the front end and returns the player's response
    """
    async def ask_for_message(self, prompt: str) -> str:
        logger.debug(f"ask_for_message called with prompt: {prompt}")
        while True:
            await self.redis.publish(self.dest, json.dumps({
                "type": "prompt_for_message",
                "prompt": prompt,
            }))
            
            raw = await self.pubsub.get_message(ignore_subscribe_messages=True, timeout=60)
            
            if raw is None:
                logger.error("No response received for ask_for_message")
                return ''
            
            data = json.loads(raw)
            
            if data.get("type") != "client_message":
                await self.redis.publish(self.dest, json.dumps({
                    "type": "error",
                    "detail": "Invalid message type"
                }))
                return ''
            
            text = (data.get("text") or "").strip()
                        
            if len(text) > 200:
                await self.redis.publish(self.dest, json.dumps({
                    "type": "error",
                    "detail": "Message too long, please keep below 200 charaacters"
                }))
                continue
            
            return text
   
    
    async def ask_for_select(self, prompt: str, options: list[str]) -> str:
        logger.debug(f"ask_for_select called with prompt: {prompt} and options: {options}")
        await self.redis.publish(self.dest, json.dumps({
            "type": "prompt_select",
            "prompt": prompt,
            "options": options,
        }))

        logger.debug("Message sent! Waiting for client selection...")

        raw = await self.pubsub.get_message()
        data = json.loads(raw)

        if data.get("type") != "client_select":
            await self.redis.publish(self.dest, json.dumps({"type": "error", "detail": "Invalid message type"}))
            return ""

        value = (data.get("value") or "").strip()

        if value not in options:
            await self.redis.publish(self.dest, json.dumps({"type": "error", "detail": "Invalid selection"}))
            return ""

        return value