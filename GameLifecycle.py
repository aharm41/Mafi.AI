import logging
import os
from typing import Protocol

from redis.asyncio import Redis

logger = logging.getLogger("game_lifecycle")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_TLS = os.getenv("REDIS_TLS", "false").lower() == "true"


class GameLoop(Protocol):
    async def gameLoop(self) -> None:
        ...


async def run_game_and_cleanup(game_manager: GameLoop, game_id: str) -> None:
    try:
        await game_manager.gameLoop()
    except Exception:
        logger.exception("Game %s terminated with an error", game_id)
    finally:
        cache = Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            ssl=REDIS_TLS,
            decode_responses=True,
        )
        try:
            # Valkey cannot store None; deleting makes GET return None.
            await cache.delete(
                game_id,
                f"game:{game_id}",
                f"game:{game_id}:players",
                f"game:{game_id}:relay-ready",
            )
        except Exception:
            logger.exception("Could not clear Valkey state for game %s", game_id)
        finally:
            await cache.aclose()
