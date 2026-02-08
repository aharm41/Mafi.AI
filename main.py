from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from GameManager import GameManager
from InputParams import InputParams
import logging

import json
import uuid
import asyncio

from GPTProfiles import PlayerType

app = FastAPI()

@app.websocket("/lobby/ws")
async def lobby_ws(ws: WebSocket):
    await ws.accept()
    logger = logging.getLogger(__name__)


    try:
        inputParams = InputParams(
            6,
            [
                PlayerType.DEFAULT_DERRICK,
                PlayerType.REFINED_REGINALD,
                PlayerType.SHIFTY_SHELBY,
                PlayerType.QUIET_QUINN,
                PlayerType.PECULIAR_POLLY
            ],
            1
        )
        
        gameManager = GameManager(inputParams, ws)

        funnyFile = open("funnyFile.txt", "w")

        await gameManager.gameLoop()


        print(gameManager.convoManager.getConvoSummary(), file=funnyFile)

        funnyFile.close()

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected.")
        return
    except Exception as e:
        logger.exception("Unhandled exception in lobby_ws")
        await ws.send_text(json.dumps({
            "type": "error",
            "detail": "An internal server error occurred."
        }))
        return